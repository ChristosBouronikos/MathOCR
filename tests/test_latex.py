"""LaTeX utility tests for MathOCR by Bouronikos Christos <chrisbouronikos@gmail.com>.

Support the project at https://paypal.me/christosbouronikos. Everything here
is pure string logic; no model weights are involved.
"""

from backend.latex import (
    clean_latex,
    extract_math,
    normalize_for_comparison,
    similarity,
    structure_score,
    tokenize,
)


def test_clean_latex_removes_only_outer_delimiters() -> None:
    assert clean_latex(r"\[ \frac{a}{b} \]") == r"\frac{a}{b}"
    assert clean_latex(r"$$x$$") == "x"
    assert clean_latex(r"x + y") == "x + y"


def test_tokenize_splits_commands_and_characters() -> None:
    assert tokenize(r"\frac{a}{b}") == ["\\frac", "{", "a", "}", "{", "b", "}"]


def test_normalization_ignores_cosmetic_differences() -> None:
    styled = r"\left( \dfrac{a}{b} \right) + \, x"
    plain = r"( \frac{a}{b} ) + x"
    assert normalize_for_comparison(styled) == normalize_for_comparison(plain)


def test_similarity_reflects_agreement() -> None:
    assert similarity(r"\frac{a}{b}", r"\dfrac{a}{b}") == 1.0
    assert similarity(r"\frac{a}{b}", r"\frac{a}{c}") > 0.6
    assert similarity(r"\frac{a}{b}", r"\int_0^1 e^x dx") < 0.5


def test_structure_score_penalizes_unbalanced_braces() -> None:
    assert structure_score(r"\frac{a}{b}") == 1.0
    assert structure_score(r"\frac{a}{b") < 1.0
    assert structure_score(r"\left( x") < 1.0
    assert structure_score("") == 0.0


def test_structure_score_penalizes_degenerate_repetition() -> None:
    healthy = r"x_1 + x_2 + x_3 + x_4 + x_5 + x_6 + x_7 + x_8 + x_9"
    degenerate = r"\cdot \cdot" + r" \cdot" * 30
    assert structure_score(healthy) == 1.0
    assert structure_score(degenerate) < 0.5


def test_extract_math_supports_inline_and_display_delimiters() -> None:
    source = r"Text $x^2 + 1$ then $$\int_0^1 x\,dx$$ and \[a=b\]."
    assert extract_math(source) == [r"x^2 + 1", r"\int_0^1 x\,dx", "a=b"]
