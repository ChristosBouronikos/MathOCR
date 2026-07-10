# OCR engine notes

Prepared for MathOCR by **Bouronikos Christos** ([chrisbouronikos@gmail.com](mailto:chrisbouronikos@gmail.com)). Support continued development with a [PayPal donation](https://paypal.me/christosbouronikos).

## What ships today

MathOCR runs several recognizers locally. Math formulas are read by an **ensemble that votes**; page text (Greek + English) is read by Tesseract; a full page can be reconstructed into text + math.

| Component | Model | License | Role | Size |
|---|---|---|---|---|
| `pix2text-mfr` | [Pix2Text MFR-1.5](https://github.com/breezedeus/Pix2Text) (ONNX) | MIT | **Default** formula recognizer; also supplies the MFD-1.5 math-region detector | ≈ 190 MB |
| `pix2tex` | [pix2tex / LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR) | MIT | Second opinion (different architecture) | ≈ 115 MB |
| `rapid-latex` | [RapidLaTeXOCR](https://github.com/RapidAI/RapidLatexOCR) (ONNX) | Apache-2.0 | Fast tie-breaker; same family as pix2tex so its agreement is discounted | ≈ 170 MB |
| `tesseract` | [Tesseract](https://github.com/tesseract-ocr/tesseract) `ell+eng` | Apache-2.0 | Page text for **document** mode (Greek + English) | ≈ 5 MB data + program |
| `nougat` *(optional)* | [Nougat](https://github.com/facebookresearch/nougat) | code MIT / weights CC-BY-NC | Alternative English document reader; **never bundled** | ≈ 1.4 GB |

## Modes

- **`formula`** — the whole image is one equation; the math ensemble reads it directly.
- **`mixed`** — the MFD detector finds the equations on a page, fragments are merged, each region is read by the ensemble, and only the equations are returned.
- **`document`** — as `mixed`, plus Tesseract reads the surrounding Greek/English text; text lines and formulas are interleaved by reading order into editable Markdown (`backend/engines.py::reconstruct_markdown`), which Pandoc turns into a Word document with body text and native OMML equations. With `doc_engine=nougat` an installed Nougat model reads the page in one pass instead (English papers).

## Why formulas no longer split

Math detectors report one tall construction — a big fraction, a matrix — as several partial boxes. `backend/geometry.py` merges overlapping, side-by-side, and stacked fragments back into whole regions before recognition, and treats the whole image as a single formula when one region dominates it. That is the fix for the "equations split into parts" behavior.

## The ensemble vote (`backend/engines.py::vote`)

1. Every selected engine reads the same crop.
2. Outputs are normalized in `backend/latex.py` (spacing commands, `\dfrac`↔`\frac`, `x^{2}`↔`x^2`, font wrappers).
3. Each candidate is scored on: the engine's reliability prior, structural sanity (balanced braces, no degenerate repetition loops), and weighted agreement with the *other* engines. Same-family agreement is discounted.
4. The winner is returned with a confidence; disagreeing readings become selectable alternatives in the UI.

The user can override the vote and pin a single engine from the interface.

## Engines evaluated and not shipped by default

| Engine | Why |
|---|---|
| [texify](https://github.com/VikParuchuri/texify) | GPL-3.0 — cannot be bundled in the MIT app; pins `Pillow<11`. |
| [TexTeller](https://github.com/OleehyO/TexTeller) | Depends on `ray[serve]` + `streamlit`; does not survive PyInstaller. |
| [UniMERNet](https://github.com/opendatalab/UniMERNet) | Pins `timm` incompatibly with pix2tex; needs system ImageMagick. |
| [PaddleOCR-VL / PP-FormulaNet](https://github.com/PaddlePaddle/PaddleOCR) | PaddlePaddle runtime is heavy and hard to freeze on macOS arm64. |
| [MinerU](https://github.com/opendatalab/MinerU), [DeepSeek-OCR](https://github.com/deepseek-ai/DeepSeek-OCR) | Document-pipeline scale; DeepSeek's recipe is CUDA/FlashAttention-focused. Good future external-service adapters. |

**Greek text:** EasyOCR was evaluated first but its 86 supported languages do **not** include Greek, so Tesseract (`ell`) is used instead.

## Adapter contract

A formula engine implements a tiny interface, so new engines drop in without touching the HTTP layer:

```python
class FormulaEngine(Protocol):
    id: str        # e.g. "pix2text-mfr"
    family: str    # engines in one family vote with a discount

    def recognize(self, image: Image.Image) -> Candidate: ...
```

`Candidate(engine, latex, model_score)` feeds the vote; the pipeline returns `RegionResult` objects (winner, confidence, alternatives, source box). Before adding an engine, verify:

1. Model loading is lazy and `/api/health` stays fast.
2. Weights download into the MathOCR store (`backend/model_store.py`), **never** into the package directory (read-only in an installed app).
3. PDF page limits and memory stay bounded; temporary files are deleted.
4. Model and code licenses permit the intended distribution.
5. A CPU/Mac failure produces a clear message rather than silently reaching for the cloud.
