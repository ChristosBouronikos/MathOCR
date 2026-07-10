"""Local FastAPI service for MathOCR.

Created by Bouronikos Christos <chrisbouronikos@gmail.com>.
Support this open-source project at https://paypal.me/christosbouronikos.

This service intentionally binds to localhost in the documented commands. The
browser UI can be hosted by GitHub Pages while private documents are processed
on the user's own computer. Recognition itself lives in ``backend.engines``;
this module validates uploads, routes them through the pipeline, exports Word
documents through Pandoc, and manages the on-disk model storage.
"""

from __future__ import annotations

import io
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Literal

import pypdfium2 as pdfium
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field, field_validator
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from backend import model_store

# Engine caches must be redirected below the MathOCR model folder before any
# ML package gets imported, otherwise they fall back to scattered defaults.
model_store.configure_model_environment()

# The desktop app has no visible console, so a log file next to the model
# cache is the only way a user can hand us a traceback when something fails.
_log_path = model_store.default_cache_root().parent / "logs" / "mathocr.log"
_log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(_log_path, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("mathocr")

from backend.engines import (  # noqa: E402  (environment must be configured first)
    ENGINE_LABELS,
    ENGINE_ORDER,
    EngineRegistry,
    MathPipeline,
    can_install_packages,
    installed_engine_ids,
    nougat_available,
    nougat_ready,
    text_engine_available,
)

# Storage components shown in the model manager: the math engines plus the text
# engine and the optional Nougat add-on. Each maps to a folder in the store.
STORAGE_COMPONENTS = (*ENGINE_ORDER, "tesseract", "nougat")

AUTHOR = "Bouronikos Christos"
AUTHOR_EMAIL = "chrisbouronikos@gmail.com"
DONATION_URL = "https://paypal.me/christosbouronikos"
FILENAME_SUFFIX = f"by {AUTHOR}"  # every exported file carries the author's name
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_FILES = 12
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
PDF_RENDER_SCALE = 2.8  # ≈200 dpi; complicated formulas need the extra pixels


def application_root() -> Path:
    """Return the source root or PyInstaller's extracted resource directory."""

    frozen_root = getattr(sys, "_MEIPASS", None)
    return Path(frozen_root) if frozen_root else Path(__file__).resolve().parent.parent


APP_ROOT = application_root()


def find_pandoc() -> str | None:
    """Find Pandoc from an override, a desktop bundle, pypandoc-binary, or PATH."""

    override = os.getenv("MATHOCR_PANDOC_PATH")
    if override and Path(override).is_file():
        return override

    executable = "pandoc.exe" if sys.platform == "win32" else "pandoc"
    bundled_candidates = (
        APP_ROOT / "vendor" / "pandoc" / executable,
        APP_ROOT / "pypandoc" / "files" / executable,
    )
    for candidate in bundled_candidates:
        if candidate.is_file():
            return str(candidate)

    # pypandoc-binary carries a platform Pandoc executable inside its package.
    try:
        import pypandoc

        packaged = Path(pypandoc.get_pandoc_path())
        if packaged.is_file():
            return str(packaged)
    except (ImportError, OSError):
        pass
    return shutil.which("pandoc")


app = FastAPI(
    title="MathOCR local API",
    description="Local image/PDF mathematics recognition and editable Word equation export.",
    version="1.0.0",
    contact={"name": AUTHOR, "email": AUTHOR_EMAIL, "url": DONATION_URL},
)

# Localhost covers a separately served frontend; the regex covers a deployed Pages site.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ],
    allow_origin_regex=r"https://[A-Za-z0-9-]+\.github\.io",
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

registry = EngineRegistry(device=os.getenv("MATHOCR_DEVICE", "cpu"))
pipeline = MathPipeline(registry)


class AlternativeReading(BaseModel):
    """A different engine's reading of the same region, offered for review."""

    engine: str
    latex: str


class EquationResult(BaseModel):
    """JSON representation consumed by the static frontend."""

    source: str
    page: int | None = None
    latex: str
    confidence: float | None = None
    engine: str
    kind: Literal["isolated", "embedded", "full"] = "isolated"
    region: tuple[int, int, int, int] | None = None
    alternatives: list[AlternativeReading] = Field(default_factory=list)


class DocumentResult(BaseModel):
    """One reconstructed page of text + math, as editable Markdown."""

    source: str
    page: int | None = None
    markdown: str


class OcrResponse(BaseModel):
    """Combined result for all uploaded source files."""

    results: list[EquationResult]
    documents: list[DocumentResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocxRequest(BaseModel):
    """Reviewed content submitted for Pandoc conversion.

    Provide ``markdown`` for a full document (text + equations, from document
    mode) or ``equations`` for a stack of display equations only.
    """

    title: str = Field(default="MathOCR equations", max_length=120)
    equations: list[str] = Field(default_factory=list, max_length=500)
    markdown: str | None = Field(default=None, max_length=200_000)

    @field_validator("equations")
    @classmethod
    def validate_equations(cls, equations: list[str]) -> list[str]:
        cleaned = [equation.strip() for equation in equations]
        if any(not equation for equation in cleaned):
            raise ValueError("Equations must not be empty")
        if any(len(equation) > 20_000 for equation in cleaned):
            raise ValueError("An equation is unreasonably long")
        return cleaned

    @field_validator("markdown")
    @classmethod
    def validate_markdown(cls, markdown: str | None) -> str | None:
        if markdown is not None and not markdown.strip():
            return None
        return markdown

    def require_content(self) -> None:
        if not self.equations and not (self.markdown and self.markdown.strip()):
            raise ValueError("Provide equations or markdown to export")


class EngineStorage(BaseModel):
    """Storage panel row: one engine's install/download/size status."""

    id: str
    label: str
    role: Literal["math", "text", "optional"]
    installed: bool
    loaded: bool
    bytes: int
    # ``downloadable`` marks an optional engine (Nougat) the user can fetch with
    # a button; ``ready`` means it is fully installed and usable right now.
    downloadable: bool = False
    ready: bool = True


class ModelsResponse(BaseModel):
    """Everything the interface needs to show and manage model storage."""

    cache_root: str
    engines: list[EngineStorage]
    total_bytes: int


class DeleteModelsResponse(BaseModel):
    """Outcome of a storage cleanup, mirrored back to the interface."""

    freed_bytes: int
    deleted_paths: list[str]
    failed_paths: list[str]


@app.get("/api/health")
def health() -> dict[str, object]:
    """Report readiness without loading any multi-hundred-megabyte model."""

    return {
        "status": "ok",
        "version": app.version,
        "pandoc": find_pandoc() is not None,
        "engines_installed": installed_engine_ids(),
        "loaded_engines": registry.loaded,
        "text_available": text_engine_available(),
        "nougat_available": nougat_available(),
        "nougat_ready": nougat_ready(),
        "nougat_installable": can_install_packages(),
        "author": AUTHOR,
        "donate": DONATION_URL,
        "log_file": str(_log_path),
    }


def safe_filename(name: str | None) -> str:
    """Strip paths and control characters from a browser-provided filename."""

    base = Path(name or "upload").name
    return re.sub(r"[^A-Za-z0-9._ ()-]", "_", base)[:180]


async def read_upload(upload: UploadFile) -> tuple[str, bytes]:
    """Read an upload with an explicit size cap and basic extension validation."""

    filename = safe_filename(upload.filename)
    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {filename}")
    data = await upload.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail=f"{filename} is larger than 25 MB")
    if not data:
        raise HTTPException(status_code=400, detail=f"{filename} is empty")
    return filename, data


def normalized_image(data: bytes) -> Image.Image:
    """Decode an image, apply EXIF rotation, and flatten transparency onto white."""

    try:
        source = Image.open(io.BytesIO(data))
        source.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded image could not be decoded") from exc
    source = ImageOps.exif_transpose(source)
    if source.mode in {"RGBA", "LA"} or (source.mode == "P" and "transparency" in source.info):
        rgba = source.convert("RGBA")
        canvas = Image.new("RGBA", rgba.size, "white")
        canvas.alpha_composite(rgba)
        return canvas.convert("RGB")
    return source.convert("RGB")


def pdf_pages(data: bytes, page_limit: int) -> tuple[list[tuple[int, Image.Image]], bool]:
    """Render bounded PDF pages at a recognition-friendly resolution."""

    try:
        document = pdfium.PdfDocument(data)
    except Exception as exc:  # pypdfium2 exposes several backend-specific errors.
        raise ValueError("The uploaded PDF could not be opened") from exc

    total_pages = len(document)
    rendered: list[tuple[int, Image.Image]] = []
    try:
        for page_index in range(min(total_pages, page_limit)):
            page = document[page_index]
            bitmap = page.render(scale=PDF_RENDER_SCALE)
            image = bitmap.to_pil().convert("RGB")
            rendered.append((page_index + 1, image.copy()))
            bitmap.close()
            page.close()
    finally:
        document.close()
    return rendered, total_pages > page_limit


def recognize_file(
    filename: str, data: bytes, mode: str, page_limit: int, engine: str, doc_engine: str
) -> tuple[list[EquationResult], list[DocumentResult], list[str]]:
    """Run one validated file through the recognition pipeline."""

    is_pdf = filename.lower().endswith(".pdf")
    warnings: list[str] = []
    if is_pdf:
        pages, truncated = pdf_pages(data, page_limit)
        if truncated:
            warnings.append(f"{filename}: only the first {page_limit} pages were processed")
    else:
        pages = [(1, normalized_image(data))]

    results: list[EquationResult] = []
    documents: list[DocumentResult] = []
    text_missing = False
    for page_number, image in pages:
        try:
            outcome = pipeline.process(image, mode, engine, doc_engine)
        finally:
            image.close()
        page_ref = page_number if is_pdf else None
        for region in outcome.regions:
            if not region.latex:
                continue
            results.append(
                EquationResult(
                    source=filename,
                    page=page_ref,
                    latex=region.latex,
                    confidence=region.confidence,
                    engine=region.engine,
                    kind=region.kind,
                    region=region.box,
                    alternatives=[
                        AlternativeReading(engine=alternative.engine, latex=alternative.latex)
                        for alternative in region.alternatives
                    ],
                )
            )
        if outcome.markdown:
            documents.append(
                DocumentResult(source=filename, page=page_ref, markdown=outcome.markdown)
            )
        if mode == "document" and not outcome.text_available:
            text_missing = True

    if text_missing:
        warnings.append(
            f"{filename}: page text could not be read (Tesseract not available); "
            "only equations were extracted"
        )
    return results, documents, warnings


@app.post("/api/ocr", response_model=OcrResponse)
async def ocr(
    files: Annotated[list[UploadFile], File(description="PDF and image source files")],
    mode: Annotated[Literal["document", "mixed", "formula"], Form()] = "mixed",
    engine: Annotated[str, Form()] = "auto",
    doc_engine: Annotated[Literal["layout", "nougat"], Form()] = "layout",
    max_pdf_pages: Annotated[int, Form(ge=1, le=20)] = 10,
) -> OcrResponse:
    """Recognize equations (and, in document mode, text) off the event loop.

    ``mode``: ``document`` reconstructs the whole page (Greek/English text +
    math), ``mixed`` returns only the equations on a page, ``formula`` treats
    the whole image as one equation. ``engine`` is ``auto`` for the
    cross-checked vote or a single engine id. ``doc_engine`` chooses the
    document reader: ``layout`` (Tesseract + math) or ``nougat``.
    """

    if not files or len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Upload between 1 and {MAX_FILES} files")

    uploads = [await read_upload(upload) for upload in files]
    results: list[EquationResult] = []
    documents: list[DocumentResult] = []
    warnings: list[str] = []
    try:
        for filename, data in uploads:
            file_results, file_documents, file_warnings = await run_in_threadpool(
                recognize_file, filename, data, mode, max_pdf_pages, engine, doc_engine
            )
            results.extend(file_results)
            documents.extend(file_documents)
            warnings.extend(file_warnings)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # This is a local desktop app processing the user's own files, so the
        # real message (often a missing model path) is safe to show and is
        # the only diagnostic a user without a visible console can report.
        logger.exception("Recognition failed for %s", [name for name, _ in uploads])
        raise HTTPException(
            status_code=500, detail=f"Recognition failed: {type(exc).__name__}: {exc}"
        ) from exc
    return OcrResponse(results=results, documents=documents, warnings=warnings)


@app.get("/api/models", response_model=ModelsResponse)
def models_inventory() -> ModelsResponse:
    """Report where models live and how much disk space each engine uses."""

    sizes: dict[str, int] = {}
    for entry in model_store.store_entries():
        sizes[entry.engine] = sizes.get(entry.engine, 0) + entry.bytes

    installed = set(installed_engine_ids())
    loaded = set(registry.loaded)
    text_ready = text_engine_available()
    nougat_installed = nougat_available()
    nougat_is_ready = nougat_ready()

    def is_installed(component: str) -> bool:
        if component == "tesseract":
            return text_ready
        if component == "nougat":
            return nougat_installed
        return component in installed

    engines = [
        EngineStorage(
            id=component,
            label=ENGINE_LABELS[component],
            role=_component_role(component),
            installed=is_installed(component),
            loaded=component in loaded,
            bytes=sizes.get(_storage_key(component), 0),
            downloadable=(component == "nougat"),
            ready=(nougat_is_ready if component == "nougat" else is_installed(component)),
        )
        for component in STORAGE_COMPONENTS
    ]
    return ModelsResponse(
        cache_root=str(model_store.default_cache_root()),
        engines=engines,
        total_bytes=sum(sizes.values()),
    )


def _component_role(component: str) -> str:
    if component == "tesseract":
        return "text"
    if component == "nougat":
        return "optional"
    return "math"


def _storage_key(component: str) -> str:
    """Map a component id to its folder key in the model store."""

    return "pix2text" if component == "pix2text-mfr" else component


@app.post("/api/models/download")
async def download_models() -> dict[str, object]:
    """Fetch every installed engine's model files ahead of first recognition.

    This can take several minutes on a slow connection; the interface presents
    it as an explicit "prepare models" step so first OCR feels instant.
    """

    def fetch() -> list[str]:
        prepared: list[str] = []
        installed = set(installed_engine_ids())
        if "pix2text-mfr" in installed:
            model_store.ensure_pix2text_models()
            prepared.append("pix2text-mfr")
        if "pix2tex" in installed:
            model_store.ensure_pix2tex_weights()
            prepared.append("pix2tex")
        if "rapid-latex" in installed:
            model_store.ensure_rapid_latex_weights()
            prepared.append("rapid-latex")
        if text_engine_available():
            model_store.ensure_tesseract_langs()
            prepared.append("tesseract")
        # Nougat is fetched only when its optional package is installed; its
        # non-commercial weights are never downloaded implicitly otherwise.
        if nougat_available():
            model_store.ensure_nougat_model()
            prepared.append("nougat")
        return prepared

    try:
        prepared = await run_in_threadpool(fetch)
    except Exception as exc:
        logger.exception("Model download failed")
        raise HTTPException(
            status_code=502, detail=f"Model download failed: {type(exc).__name__}: {exc}"
        ) from exc
    return {"prepared": prepared}


NOUGAT_PIP_TARGET = "nougat-ocr>=0.1.17,<1"


@app.post("/api/models/nougat/install")
async def install_nougat() -> dict[str, object]:
    """Install the optional Nougat engine on demand, from a UI button.

    Installs the ``nougat-ocr`` package if it is missing (only possible when
    MathOCR runs from a normal Python, not a frozen bundle) and then downloads
    its checkpoint. The weights are CC-BY-NC, so this only runs when the user
    explicitly asks for it. Once finished, Nougat appears in the document
    reader menu.
    """

    def work() -> dict[str, object]:
        import importlib

        if not nougat_available():
            if not can_install_packages():
                raise RuntimeError(
                    "Nougat cannot be installed into the packaged app. Run MathOCR "
                    "from source (run.command / run.bat) to add it, or use a "
                    "Nougat-enabled build."
                )
            completed = subprocess.run(
                [sys.executable, "-m", "pip", "install", NOUGAT_PIP_TARGET],
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip()[-500:] or "pip install failed")
            importlib.invalidate_caches()

        model_store.ensure_nougat_model()
        registry.unload_all()  # pick up the newly available package on next use
        return {"ready": nougat_ready()}

    try:
        result = await run_in_threadpool(work)
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Nougat installation timed out") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Nougat installation failed")
        raise HTTPException(
            status_code=502, detail=f"Nougat installation failed: {type(exc).__name__}: {exc}"
        ) from exc
    return result


@app.delete("/api/models", response_model=DeleteModelsResponse)
def delete_models(engine: str | None = None) -> DeleteModelsResponse:
    """Delete downloaded model files to free disk space.

    Without a query parameter every engine's storage is removed. Engines are
    unloaded from memory first so open file handles do not block deletion.
    """

    known = {_storage_key(component) for component in STORAGE_COMPONENTS}
    if engine is not None and engine not in known:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {engine}")

    registry.unload_all()
    report = model_store.delete_engine_storage(engine)
    return DeleteModelsResponse(
        freed_bytes=report.freed_bytes,
        deleted_paths=report.deleted_paths,
        failed_paths=report.failed_paths,
    )


def markdown_document(request: DocxRequest) -> str:
    """Build Pandoc Markdown with display-math delimiters for native OMML output.

    A ``markdown`` payload (document mode) is used verbatim under the title so
    body text and equations both survive to Word; otherwise the equations are
    stacked as display-math blocks with proper spacing for math recognition.
    """

    safe_title = request.title.replace("\n", " ").strip() or "MathOCR equations"
    blocks = [f"# {safe_title}", ""]
    if request.markdown and request.markdown.strip():
        blocks.append(request.markdown.strip())
    else:
        for equation in request.equations:
            clean_eq = equation.strip()
            if clean_eq.startswith("$$") and clean_eq.endswith("$$"):
                clean_eq = clean_eq[2:-2].strip()
            blocks.extend(("", "$$", clean_eq, "$$", ""))
    return "\n".join(blocks)


def export_filename(title: str, extension: str) -> str:
    """Build a download name that always credits the author at the end.

    Example: ``MathOCR equations by Bouronikos Christos.docx``.
    """

    base = re.sub(r"[^\w ()-]", " ", title, flags=re.UNICODE)  # \w keeps Greek letters
    base = re.sub(r"\s+", " ", base).strip() or "MathOCR equations"
    return f"{base[:80]} {FILENAME_SUFFIX}.{extension}"


def remove_tree(path: str) -> None:
    """Delete only the private temporary directory created for one export."""

    shutil.rmtree(path, ignore_errors=True)


@app.post("/api/export/docx")
async def export_docx(request: DocxRequest) -> FileResponse:
    """Convert reviewed TeX to a Word document containing editable OMML equations."""

    try:
        request.require_content()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    pandoc = find_pandoc()
    if not pandoc:
        raise HTTPException(status_code=503, detail="Pandoc is not installed or is not on PATH")

    temp_dir = tempfile.mkdtemp(prefix="mathocr-")
    markdown_path = Path(temp_dir, "equations.md")
    output_path = Path(temp_dir, "equations.docx")
    markdown_path.write_text(markdown_document(request), encoding="utf-8")

    try:
        completed = await run_in_threadpool(
            subprocess.run,
            [
                pandoc,
                "--from=markdown+tex_math_dollars",
                "--to=docx",
                "--standalone",
                str(markdown_path),
                "--output",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        remove_tree(temp_dir)
        raise HTTPException(status_code=504, detail="Pandoc export timed out") from exc

    if completed.returncode != 0 or not output_path.exists():
        remove_tree(temp_dir)
        detail = completed.stderr.strip()[-600:] or "Pandoc did not create a document"
        raise HTTPException(status_code=422, detail=f"Word export failed: {detail}")

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=export_filename(request.title, "docx"),
        background=BackgroundTask(remove_tree, temp_dir),
    )


# Mount last so /api routes win. This makes one Uvicorn process sufficient locally,
# while the same frontend directory remains independently deployable to GitHub Pages.
FRONTEND_DIR = APP_ROOT / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
