"""Model storage management for MathOCR.

Authored by Bouronikos Christos <chrisbouronikos@gmail.com>.
Donations are welcome at https://paypal.me/christosbouronikos.

Every recognition model MathOCR downloads is kept below one per-user cache
folder. That single root makes the storage panel in the interface truthful:
sizes can be measured, and deleting an engine's folder really frees the space.

The folder is chosen per platform and can be overridden with the
``MATHOCR_MODEL_DIR`` environment variable:

- macOS:   ~/Library/Application Support/MathOCR/models
- Windows: %LOCALAPPDATA%/MathOCR/models
- Linux:   $XDG_CACHE_HOME/mathocr/models (default ~/.cache/mathocr/models)

pix2tex and RapidLaTeXOCR would normally download weights *into their own
package directory*, which is read-only inside an installed desktop app (for
example under Program Files). MathOCR therefore downloads those files itself,
into this cache, and hands the engines explicit paths.
"""

from __future__ import annotations

import os
import shutil
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

USER_AGENT = "MathOCR/1.0 (+https://github.com/ChristosBouronikos/MathOCR)"

# Upstream release files. Versions are pinned: both projects publish their
# weights once under a fixed tag, so these URLs are stable.
PIX2TEX_FILES = {
    "weights.pth": "https://github.com/lukas-blecher/LaTeX-OCR/releases/download/v0.0.1/weights.pth",
    "image_resizer.pth": "https://github.com/lukas-blecher/LaTeX-OCR/releases/download/v0.0.1/image_resizer.pth",
}
RAPID_LATEX_FILES = {
    "encoder.onnx": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/encoder.onnx",
    "decoder.onnx": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/decoder.onnx",
    "image_resizer.onnx": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/image_resizer.onnx",
    "tokenizer.json": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/tokenizer.json",
}

# Tesseract language data (tessdata_fast, Apache-2.0). Greek plus English cover
# the expected inputs; the math itself is read by the LaTeX engines. Files are
# small (~1–4 MB each) and download on demand into the MathOCR store.
TESSERACT_BASE = "https://github.com/tesseract-ocr/tessdata_fast/raw/main"
TESSERACT_LANGS = ("ell", "eng")


def default_cache_root() -> Path:
    """Return the per-platform folder that holds every downloaded model."""

    override = os.getenv("MATHOCR_MODEL_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "MathOCR" / "models"
    if sys.platform == "win32":
        local = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local) / "MathOCR" / "models"
    xdg = os.getenv("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(xdg) / "mathocr" / "models"


def configure_model_environment() -> Path:
    """Point every engine's own cache mechanism below the MathOCR root.

    Must run before any engine module is imported. Explicit user-provided
    values for the underlying variables are respected.
    """

    root = default_cache_root()
    os.environ.setdefault("PIX2TEXT_HOME", str(root / "pix2text"))
    os.environ.setdefault("CNSTD_HOME", str(root / "cnstd"))
    os.environ.setdefault("CNOCR_HOME", str(root / "cnocr"))
    # Nougat (optional) reads its checkpoint from this directory when present.
    os.environ.setdefault("NOUGAT_CHECKPOINT", str(root / "nougat"))
    return root


def tesseract_data_dir() -> Path:
    """Return the tessdata directory that holds MathOCR's language files."""

    return default_cache_root() / "tesseract" / "tessdata"


def _download(url: str, destination: Path) -> None:
    """Stream one file to disk atomically; partial downloads never survive."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, open(partial, "wb") as sink:
            shutil.copyfileobj(response, sink, length=1024 * 256)
        if partial.stat().st_size == 0:
            raise OSError(f"Downloaded file is empty: {url}")
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def _ensure_files(directory: Path, files: dict[str, str]) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for name, url in files.items():
        target = directory / name
        if not target.is_file() or target.stat().st_size == 0:
            _download(url, target)
        resolved[name] = target
    return resolved


def ensure_pix2tex_weights() -> dict[str, Path]:
    """Download pix2tex checkpoint files into the MathOCR cache if missing."""

    return _ensure_files(default_cache_root() / "pix2tex", PIX2TEX_FILES)


def ensure_rapid_latex_weights() -> dict[str, Path]:
    """Download RapidLaTeXOCR ONNX files into the MathOCR cache if missing."""

    return _ensure_files(default_cache_root() / "rapid-latex-ocr", RAPID_LATEX_FILES)


def ensure_pix2text_models() -> list[Path]:
    """Download the Pix2Text detector and recognizer weights if missing.

    Reuses pix2text's own downloader so file layout stays exactly what the
    library expects at load time. Requires the pix2text package.
    """

    from pix2text.consts import AVAILABLE_MODELS, MODEL_VERSION
    from pix2text.utils import data_dir, prepare_model_files

    prepared: list[Path] = []
    for model_name in ("mfd-1.5", "mfr-1.5"):
        model_info = AVAILABLE_MODELS.get_info(model_name, "onnx")
        model_dir = Path(data_dir()) / MODEL_VERSION / model_info["local_model_id"]
        if not (model_dir.is_dir() and any(model_dir.rglob("*"))):
            prepare_model_files(data_dir(), model_info)
        prepared.append(model_dir)
    return prepared


def ensure_tesseract_langs() -> Path:
    """Download the Greek and English tessdata files if missing.

    Returns the tessdata directory to pass to Tesseract as ``--tessdata-dir``.
    """

    directory = tesseract_data_dir()
    files = {f"{lang}.traineddata": f"{TESSERACT_BASE}/{lang}.traineddata" for lang in TESSERACT_LANGS}
    _ensure_files(directory, files)
    return directory


def ensure_nougat_model() -> Path:
    """Download the optional Nougat checkpoint into the MathOCR store.

    Requires the optional ``nougat-ocr`` package. Nougat weights are licensed
    CC-BY-NC (non-commercial), which is why they are never bundled and are
    downloaded only when the user explicitly enables the engine.
    """

    from nougat.utils.checkpoint import get_checkpoint

    target = default_cache_root() / "nougat"
    target.mkdir(parents=True, exist_ok=True)
    # model_tag "0.1.0-small" is the CPU-friendly checkpoint.
    return Path(get_checkpoint(target, model_tag="0.1.0-small", download=True))


def directory_size(path: Path) -> int:
    """Total bytes of all files below ``path``; 0 when it does not exist."""

    if not path.exists():
        return 0
    total = 0
    for entry in path.rglob("*"):
        try:
            if entry.is_file() and not entry.is_symlink():
                total += entry.stat().st_size
        except OSError:
            continue
    return total


@dataclass(slots=True)
class StoreEntry:
    """One deletable model folder shown in the interface's storage panel."""

    engine: str
    path: Path
    bytes: int = 0
    legacy: bool = False

    def measure(self) -> StoreEntry:
        self.bytes = directory_size(self.path)
        return self


def store_entries() -> list[StoreEntry]:
    """Enumerate every folder MathOCR may occupy, including legacy locations.

    The legacy entries cover caches created by earlier MathOCR versions (or by
    using the libraries directly) in their default home-directory locations,
    so "delete everything" genuinely returns the disk space.
    """

    root = default_cache_root()
    entries = [
        StoreEntry("pix2text", Path(os.getenv("PIX2TEXT_HOME", str(root / "pix2text")))),
        StoreEntry("pix2tex", root / "pix2tex"),
        StoreEntry("rapid-latex", root / "rapid-latex-ocr"),
        StoreEntry("tesseract", root / "tesseract"),
        StoreEntry("nougat", Path(os.getenv("NOUGAT_CHECKPOINT", str(root / "nougat")))),
    ]

    legacy_candidates = {
        "pix2text": Path.home() / ".pix2text",
        "pix2tex": None,
        "rapid-latex": None,
    }
    if sys.platform == "win32" and os.getenv("APPDATA"):
        legacy_candidates["pix2text"] = Path(os.environ["APPDATA"]) / "pix2text"
    legacy_pix2text = legacy_candidates["pix2text"]
    already_listed = {entry.path.resolve() for entry in entries if entry.path.exists()}
    if (
        legacy_pix2text is not None
        and legacy_pix2text.exists()
        and legacy_pix2text.resolve() not in already_listed
    ):
        entries.append(StoreEntry("pix2text", legacy_pix2text, legacy=True))

    return [entry.measure() for entry in entries]


@dataclass(slots=True)
class DeletionReport:
    """Outcome of a storage cleanup request."""

    freed_bytes: int = 0
    deleted_paths: list[str] = field(default_factory=list)
    failed_paths: list[str] = field(default_factory=list)


def delete_engine_storage(engine: str | None = None) -> DeletionReport:
    """Delete downloaded model files for one engine, or all when ``None``."""

    report = DeletionReport()
    for entry in store_entries():
        if engine is not None and entry.engine != engine:
            continue
        if not entry.path.exists():
            continue
        size = entry.bytes
        try:
            shutil.rmtree(entry.path)
            report.freed_bytes += size
            report.deleted_paths.append(str(entry.path))
        except OSError:
            # Typically Windows refusing to remove files that are memory-mapped
            # by a loaded model. The caller unloads engines first, but a still
            # undeletable folder is reported instead of raising.
            report.failed_paths.append(str(entry.path))
    return report
