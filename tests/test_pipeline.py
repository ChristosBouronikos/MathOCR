"""Pipeline and ensemble tests for MathOCR by Bouronikos Christos <chrisbouronikos@gmail.com>.

Support the project at https://paypal.me/christosbouronikos. Fake engines, a
fake detector, and a fake text engine exercise routing, merging, voting, and
document reconstruction without loading any model weights.
"""

from PIL import Image

from backend import engines as engine_module
from backend.engines import (
    Candidate,
    MathPipeline,
    RegionResult,
    TextLine,
    reconstruct_markdown,
    vote,
)
from backend.geometry import Box


class FakeEngine:
    def __init__(self, engine_id: str, latex: str) -> None:
        self.id = engine_id
        self.family = "mfr" if engine_id == "pix2text-mfr" else "latex-ocr"
        self._latex = latex
        self.calls = 0

    def recognize(self, image: Image.Image) -> Candidate:
        self.calls += 1
        return Candidate(self.id, self._latex)


class FakeDetector:
    def __init__(self, regions: list[tuple[Box, str]]) -> None:
        self._regions = regions
        self.calls = 0

    def detect(self, image: Image.Image) -> list[tuple[Box, str]]:
        self.calls += 1
        return self._regions


class FakeTextEngine:
    def __init__(self, lines: list[TextLine]) -> None:
        self._lines = lines

    def read_lines(self, image: Image.Image) -> list[TextLine]:
        return self._lines


class FakeRegistry:
    def __init__(self, engines, detector, text_engine=None) -> None:
        self._engines = engines
        self._detector = detector
        self._text_engine = text_engine

    def select_engines(self, selection: str):
        if selection and selection != "auto":
            chosen = [engine for engine in self._engines if engine.id == selection]
            return chosen or self._engines[:1]
        return self._engines

    def detector(self):
        return self._detector

    def text_engine(self):
        return self._text_engine


def test_vote_prefers_agreement_between_different_families() -> None:
    winner, confidence, alternatives = vote(
        [
            Candidate("pix2text-mfr", r"\frac{a}{b}"),
            Candidate("pix2tex", r"\dfrac{a}{b}"),
            Candidate("rapid-latex", r"a/b"),
        ]
    )
    assert winner.engine == "pix2text-mfr"
    assert confidence > 0.6
    assert [alternative.latex for alternative in alternatives] == ["a/b"]


def test_vote_rejects_degenerate_repetition() -> None:
    degenerate = r"\cdot" * 40
    winner, _confidence, _alternatives = vote(
        [
            Candidate("pix2tex", degenerate),
            Candidate("pix2text-mfr", r"\int_0^1 x^2 \, dx = \frac{1}{3}"),
        ]
    )
    assert winner.engine == "pix2text-mfr"


def test_vote_single_candidate_uses_model_score() -> None:
    winner, confidence, alternatives = vote([Candidate("pix2text-mfr", r"x^2", model_score=0.9)])
    assert winner.engine == "pix2text-mfr"
    assert confidence == 0.9
    assert alternatives == []


def make_pipeline(regions, engines, text_engine=None):
    detector = FakeDetector(regions)
    registry = FakeRegistry(engines, detector, text_engine)
    return MathPipeline(registry), detector


def test_formula_mode_skips_detection_entirely() -> None:
    pipeline, detector = make_pipeline([], [FakeEngine("pix2text-mfr", r"E=mc^2")])
    with Image.new("RGB", (400, 120), "white") as image:
        outcome = pipeline.process(image, mode="formula")
    assert detector.calls == 0
    assert [region.latex for region in outcome.regions] == [r"E=mc^2"]
    assert outcome.regions[0].kind == "full"


def test_engine_selection_pins_a_single_engine() -> None:
    mfr = FakeEngine("pix2text-mfr", r"\frac{a}{b}")
    pix = FakeEngine("pix2tex", r"a/b")
    pipeline, _detector = make_pipeline([], [mfr, pix])
    with Image.new("RGB", (400, 120), "white") as image:
        outcome = pipeline.process(image, mode="formula", engine="pix2tex")
    assert outcome.regions[0].engine == "pix2tex"
    assert mfr.calls == 0 and pix.calls == 1


def test_fragmented_crop_is_recognized_once_as_whole_image() -> None:
    fragments = [
        (Box(60, 20, 740, 150), "isolated"),
        (Box(80, 170, 720, 330), "isolated"),
    ]
    engine = FakeEngine("pix2text-mfr", r"\frac{x^2+1}{x-1}")
    pipeline, detector = make_pipeline(fragments, [engine])
    with Image.new("RGB", (800, 360), "white") as image:
        outcome = pipeline.process(image, mode="mixed")
    assert detector.calls == 1
    assert engine.calls == 1
    assert len(outcome.regions) == 1
    assert outcome.regions[0].kind == "full"


def test_mixed_mode_returns_merged_regions_with_boxes() -> None:
    page_regions = [
        (Box(200, 300, 1400, 420), "isolated"),
        (Box(200, 900, 1400, 1000), "isolated"),
        (Box(220, 1015, 1380, 1120), "isolated"),
    ]
    engine = FakeEngine("pix2text-mfr", r"y = \frac{1}{x}")
    pipeline, _detector = make_pipeline(page_regions, [engine])
    with Image.new("RGB", (1700, 2300), "white") as image:
        outcome = pipeline.process(image, mode="mixed")
    assert len(outcome.regions) == 2
    assert engine.calls == 2
    assert all(region.box is not None for region in outcome.regions)
    assert outcome.markdown is None


def test_document_mode_reconstructs_text_and_math(monkeypatch) -> None:
    monkeypatch.setattr(engine_module, "text_engine_available", lambda: True)
    page_regions = [(Box(200, 480, 1400, 620), "isolated")]
    text_lines = [
        TextLine(Box(200, 300, 1400, 360), "Έστω η συνάρτηση", 0.9),
        TextLine(Box(200, 700, 1400, 760), "για κάθε x.", 0.9),
    ]
    engine = FakeEngine("pix2text-mfr", r"f(x) = x^2")
    pipeline, _detector = make_pipeline(page_regions, [engine], FakeTextEngine(text_lines))
    with Image.new("RGB", (1700, 2300), "white") as image:
        outcome = pipeline.process(image, mode="document")
    assert outcome.markdown is not None
    assert "Έστω η συνάρτηση" in outcome.markdown
    assert "$$\nf(x) = x^2\n$$" in outcome.markdown
    order = [outcome.markdown.index(part) for part in ("Έστω", "f(x)", "για κάθε")]
    assert order == sorted(order)
    assert len(outcome.regions) == 1


def test_document_mode_without_text_engine_still_returns_math(monkeypatch) -> None:
    monkeypatch.setattr(engine_module, "text_engine_available", lambda: False)
    page_regions = [(Box(200, 480, 1400, 620), "isolated")]
    engine = FakeEngine("pix2text-mfr", r"f(x) = x^2")
    pipeline, _detector = make_pipeline(page_regions, [engine], None)
    with Image.new("RGB", (1700, 2300), "white") as image:
        outcome = pipeline.process(image, mode="document")
    assert outcome.markdown is None
    assert outcome.text_available is False
    assert len(outcome.regions) == 1


def test_reconstruct_markdown_inlines_embedded_math() -> None:
    text_lines = [TextLine(Box(100, 100, 400, 150), "The value", 0.9)]
    math = [RegionResult(latex="x^2", engine="pix2text-mfr", confidence=0.9,
                         box=(410, 100, 470, 150), kind="embedded")]
    markdown = reconstruct_markdown(text_lines, math, page_height=1000)
    assert markdown == "The value $x^2$"


def test_reconstruct_markdown_orders_rows_top_to_bottom() -> None:
    text_lines = [
        TextLine(Box(100, 400, 400, 450), "second", 0.9),
        TextLine(Box(100, 100, 400, 150), "first", 0.9),
    ]
    markdown = reconstruct_markdown(text_lines, [], page_height=1000)
    assert markdown.index("first") < markdown.index("second")


def test_trivial_inline_fragments_are_dropped() -> None:
    page_regions = [
        (Box(100, 100, 900, 220), "isolated"),
        (Box(1000, 1000, 1040, 1030), "embedded"),
    ]

    class KindAwareEngine(FakeEngine):
        def recognize(self, image: Image.Image) -> Candidate:
            self.calls += 1
            latex = r"\sum_{n=1}^{\infty} \frac{1}{n^2}" if image.width > 300 else "x"
            return Candidate(self.id, latex)

    engine = KindAwareEngine("pix2text-mfr", "")
    pipeline, _detector = make_pipeline(page_regions, [engine])
    with Image.new("RGB", (1700, 2300), "white") as image:
        outcome = pipeline.process(image, mode="mixed")
    assert len(outcome.regions) == 1
    assert outcome.regions[0].kind == "isolated"


def test_failing_engine_does_not_sink_the_request() -> None:
    class BrokenEngine(FakeEngine):
        def recognize(self, image: Image.Image) -> Candidate:
            raise RuntimeError("engine exploded")

    healthy = FakeEngine("pix2text-mfr", r"a+b")
    pipeline, _detector = make_pipeline([], [BrokenEngine("pix2tex", ""), healthy])
    with Image.new("RGB", (300, 100), "white") as image:
        outcome = pipeline.process(image, mode="formula")
    assert outcome.regions[0].latex == r"a+b"


def test_region_result_defaults() -> None:
    result = RegionResult(latex="x", engine="pix2tex", confidence=None)
    assert result.alternatives == []
    assert result.box is None
