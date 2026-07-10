"""Fast unit checks for MathOCR by Bouronikos Christos <chrisbouronikos@gmail.com>.

Support the project at https://paypal.me/christosbouronikos. These tests avoid
loading OCR model weights so they remain quick enough for GitHub Actions.
"""

import io
import shutil
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend import __version__, model_store
from backend.app import (
    DocxRequest,
    app,
    export_filename,
    find_pandoc,
    is_newer,
    markdown_document,
    parse_version,
    pdf_pages,
    safe_filename,
)
from backend.engines import resolve_math_engines

client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_release_version_surfaces_are_consistent() -> None:
    frontend = (PROJECT_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    macos_spec = (PROJECT_ROOT / "packaging" / "MathOCR.spec").read_text(encoding="utf-8")
    windows_installer = (
        PROJECT_ROOT / "packaging" / "windows" / "MathOCR.iss"
    ).read_text(encoding="utf-8")

    assert __version__ == app.version == "1.0.6"
    assert 'const APP_VERSION = "1.0.6";' in frontend
    assert '"CFBundleShortVersionString": "1.0.6"' in macos_spec
    assert '#define MyAppVersion "1.0.6"' in windows_installer


def test_release_ui_uses_fast_default_and_wires_manual_update_check() -> None:
    frontend = (PROJECT_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    page = (PROJECT_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

    assert '<option value="pix2text-mfr" selected' in page
    assert '<option value="auto"' in page
    assert 'id="checkUpdatesButton"' in page
    assert 'checkUpdatesButton.addEventListener("click", () => checkUpdate(true))' in frontend
    assert 'id="ensembleAdvice"' in page
    assert 'processingFirstRun' in frontend
    assert 'processingStillWorking' in frontend


def test_desktop_icon_assets_are_present_and_packaged() -> None:
    spec = (PROJECT_ROOT / "packaging" / "MathOCR.spec").read_text(encoding="utf-8")
    installer = (PROJECT_ROOT / "packaging" / "windows" / "MathOCR.iss").read_text(
        encoding="utf-8"
    )

    for name in ("MathOCR.ico", "MathOCR.icns", "icon-1024.png"):
        asset = PROJECT_ROOT / "packaging" / name
        assert asset.is_file()
        assert asset.stat().st_size > 0
    assert 'WINDOWS_ICON = PROJECT_ROOT / "packaging" / "MathOCR.ico"' in spec
    assert 'MACOS_ICON = PROJECT_ROOT / "packaging" / "MathOCR.icns"' in spec
    assert "SetupIconFile=packaging\\MathOCR.ico" in installer


def test_health_does_not_load_models() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["loaded_engines"] == []


def test_github_pages_origin_is_allowed_by_cors() -> None:
    response = client.get(
        "/api/health", headers={"Origin": "https://christosbouronikos.github.io"}
    )
    assert response.headers["access-control-allow-origin"] == "https://christosbouronikos.github.io"


def test_safe_filename_removes_paths_and_control_characters() -> None:
    assert safe_filename("../../private/equation\n.pdf") == "equation_.pdf"


def test_export_filename_always_credits_the_author() -> None:
    assert export_filename("MathOCR equations", "docx") == (
        "MathOCR equations by Bouronikos Christos.docx"
    )
    greek = export_filename("Εξισώσεις MathOCR", "tex")
    assert greek.startswith("Εξισώσεις MathOCR")
    assert greek.endswith("by Bouronikos Christos.tex")
    hostile = export_filename('../"weird:/title', "docx")
    assert "/" not in hostile and '"' not in hostile
    assert hostile.endswith("by Bouronikos Christos.docx")


def test_pandoc_environment_override(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    bundled = tmp_path / "pandoc"
    bundled.write_bytes(b"test executable placeholder")
    monkeypatch.setenv("MATHOCR_PANDOC_PATH", str(bundled))
    assert find_pandoc() == str(bundled)


def test_markdown_document_uses_pandoc_math_blocks() -> None:
    document = markdown_document(DocxRequest(title="My math", equations=[r"x^2", r"\frac12"]))
    assert document.startswith("# My math")
    assert "$$\nx^2\n$$" in document
    assert "$$\n\\frac12\n$$" in document


def test_markdown_document_uses_full_document_markdown() -> None:
    body = "Έστω η συνάρτηση $f(x)$.\n\n$$\nf(x) = x^2\n$$"
    document = markdown_document(DocxRequest(title="Doc", markdown=body))
    assert document.startswith("# Doc")
    assert "Έστω η συνάρτηση $f(x)$." in document
    assert "$$\nf(x) = x^2\n$$" in document


def test_docx_request_requires_some_content() -> None:
    empty = DocxRequest(title="Nothing")
    with pytest.raises(ValueError):
        empty.require_content()


def test_resolve_math_engines_handles_selection() -> None:
    # No ML packages are guaranteed in CI, so this only checks the routing shape.
    assert resolve_math_engines("auto") == resolve_math_engines("auto")
    assert resolve_math_engines("does-not-exist") == resolve_math_engines("auto")[:1]


def test_pdf_pages_renders_a_pdf_from_memory() -> None:
    source = io.BytesIO()
    Image.new("RGB", (80, 50), "white").save(source, format="PDF")
    pages, truncated = pdf_pages(source.getvalue(), page_limit=2)
    assert len(pages) == 1
    assert pages[0][0] == 1
    assert pages[0][1].mode == "RGB"
    assert truncated is False
    pages[0][1].close()


def _fake_model_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point every storage path at a temporary folder with fake weights."""

    root = tmp_path / "models"
    monkeypatch.setenv("MATHOCR_MODEL_DIR", str(root))
    monkeypatch.setenv("PIX2TEXT_HOME", str(root / "pix2text"))
    # Isolate from any real legacy cache in the developer's home directory.
    monkeypatch.setattr(model_store.Path, "home", staticmethod(lambda: tmp_path / "home"))
    (root / "pix2text" / "1.1" / "mfr-1.5-onnx").mkdir(parents=True)
    (root / "pix2text" / "1.1" / "mfr-1.5-onnx" / "model.onnx").write_bytes(b"a" * 2048)
    (root / "pix2tex").mkdir(parents=True)
    (root / "pix2tex" / "weights.pth").write_bytes(b"b" * 1024)
    return root


def test_models_inventory_reports_sizes(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _fake_model_cache(monkeypatch, tmp_path)
    response = client.get("/api/models")
    assert response.status_code == 200
    payload = response.json()
    sizes = {engine["id"]: engine["bytes"] for engine in payload["engines"]}
    assert sizes["pix2text-mfr"] == 2048
    assert sizes["pix2tex"] == 1024
    assert sizes["rapid-latex"] == 0
    assert payload["total_bytes"] == 3072


def test_models_deletion_frees_space(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    root = _fake_model_cache(monkeypatch, tmp_path)

    response = client.delete("/api/models", params={"engine": "pix2tex"})
    assert response.status_code == 200
    assert response.json()["freed_bytes"] == 1024
    assert not (root / "pix2tex").exists()
    assert (root / "pix2text").exists()

    response = client.delete("/api/models")
    assert response.status_code == 200
    assert response.json()["freed_bytes"] == 2048
    assert not (root / "pix2text").exists()


def test_models_deletion_rejects_unknown_engine() -> None:
    response = client.delete("/api/models", params={"engine": "skynet"})
    assert response.status_code == 404


def test_models_inventory_marks_nougat_downloadable() -> None:
    response = client.get("/api/models")
    nougat = next(e for e in response.json()["engines"] if e["id"] == "nougat")
    assert nougat["role"] == "optional"
    assert nougat["downloadable"] is True
    # With the package absent in CI, Nougat is not ready to use yet.
    assert nougat["ready"] is False


def test_install_nougat_downloads_weights_when_package_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import backend.app as app_module

    calls = {"weights": 0}

    monkeypatch.setattr(app_module, "nougat_available", lambda: True)
    monkeypatch.setattr(app_module, "nougat_ready", lambda: True)
    monkeypatch.setattr(
        app_module.model_store,
        "ensure_nougat_model",
        lambda: calls.__setitem__("weights", calls["weights"] + 1),
    )
    response = client.post("/api/models/nougat/install")
    assert response.status_code == 200
    assert response.json()["ready"] is True
    assert calls["weights"] == 1


def test_install_nougat_refuses_inside_frozen_app(monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app as app_module

    monkeypatch.setattr(app_module, "nougat_available", lambda: False)
    monkeypatch.setattr(app_module, "can_install_packages", lambda: False)
    response = client.post("/api/models/nougat/install")
    assert response.status_code == 422
    assert "packaged app" in response.json()["detail"]


def test_store_entries_include_legacy_pix2text(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    root = tmp_path / "models"
    monkeypatch.setenv("MATHOCR_MODEL_DIR", str(root))
    monkeypatch.setenv("PIX2TEXT_HOME", str(root / "pix2text"))
    legacy = tmp_path / "home" / ".pix2text"
    legacy.mkdir(parents=True)
    (legacy / "old-model.onnx").write_bytes(b"c" * 512)
    monkeypatch.setattr(model_store.Path, "home", staticmethod(lambda: tmp_path / "home"))

    entries = model_store.store_entries()
    legacy_entries = [entry for entry in entries if entry.legacy]
    assert len(legacy_entries) == 1
    assert legacy_entries[0].bytes == 512


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_docx_export_contains_native_word_equation_markup() -> None:
    response = client.post(
        "/api/export/docx",
        json={"title": "Test equations", "equations": [r"x^2 + y^2 = z^2"]},
    )
    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert "by%20Bouronikos%20Christos.docx" in disposition or (
        "by Bouronikos Christos.docx" in disposition
    )
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        document_xml = archive.read("word/document.xml")
    assert b"m:oMath" in document_xml


def test_export_text_saves_into_downloads(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import backend.app as app_module

    monkeypatch.setattr(app_module.Path, "home", staticmethod(lambda: tmp_path))
    response = client.post(
        "/api/export/text",
        json={"title": "Εξισώσεις", "extension": "tex", "content": "\\documentclass{article}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["saved"] is True
    saved = Path(payload["path"])
    assert saved.parent == tmp_path / "Downloads"
    assert saved.name.endswith("by Bouronikos Christos.tex")
    assert saved.read_text(encoding="utf-8") == "\\documentclass{article}"


def test_export_text_rejects_empty_content(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import backend.app as app_module

    monkeypatch.setattr(app_module.Path, "home", staticmethod(lambda: tmp_path))
    response = client.post("/api/export/text", json={"title": "x", "content": "   "})
    assert response.status_code == 422


def test_unique_destination_avoids_overwrite(tmp_path) -> None:
    from backend.app import unique_destination

    (tmp_path / "note.txt").write_text("first", encoding="utf-8")
    second = unique_destination(tmp_path, "note.txt")
    assert second.name == "note (2).txt"


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_docx_export_can_save_to_downloads(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import backend.app as app_module

    monkeypatch.setattr(app_module.Path, "home", staticmethod(lambda: tmp_path))
    response = client.post(
        "/api/export/docx",
        json={"title": "Doc", "equations": [r"x^2"], "save_to_downloads": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["saved"] is True
    saved = Path(payload["path"])
    assert saved.parent == tmp_path / "Downloads"
    assert saved.name.endswith("by Bouronikos Christos.docx")
    assert saved.is_file()


def test_parse_version_and_is_newer() -> None:
    assert parse_version("v1.0.3") == (1, 0, 3)
    assert parse_version("1.2") == (1, 2)
    assert parse_version("garbage") == (0,)
    assert is_newer("1.0.3", "1.0.2") is True
    assert is_newer("v1.1.0", "1.0.9") is True
    assert is_newer("1.0.2", "1.0.2") is False
    assert is_newer("1.0.1", "1.0.2") is False


def test_update_check_reports_a_newer_release(monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app as app_module

    fake_asset = {"name": "MathOCR-Setup.exe", "browser_download_url": "https://x/y", "size": 42}
    monkeypatch.setattr(
        app_module,
        "fetch_latest_release",
        lambda: {"tag_name": "v999.0.0", "html_url": "https://notes", "assets": [fake_asset]},
    )
    monkeypatch.setattr(app_module, "platform_asset", lambda assets: fake_asset)

    payload = client.get("/api/update/check").json()
    assert payload["latest"] == "999.0.0"
    assert payload["update_available"] is True
    assert payload["asset_name"] == "MathOCR-Setup.exe"
    # Running under pytest the app is not frozen, so it cannot self-install.
    assert payload["can_install"] is False


def test_update_check_ignores_same_or_older_release(monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app as app_module

    monkeypatch.setattr(
        app_module,
        "fetch_latest_release",
        lambda: {"tag_name": "v0.0.1", "assets": []},
    )
    payload = client.get("/api/update/check").json()
    assert payload["update_available"] is False


def test_update_install_refuses_outside_frozen_app() -> None:
    # Not frozen under pytest, so the endpoint must refuse before any download
    # or process exit is attempted.
    response = client.post("/api/update/install")
    assert response.status_code == 422
    assert "packaged app" in response.json()["detail"]
