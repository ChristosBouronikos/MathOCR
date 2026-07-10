# -*- mode: python ; coding: utf-8 -*-
# MathOCR PyInstaller recipe by Bouronikos Christos <chrisbouronikos@gmail.com>.
# Support development: https://paypal.me/christosbouronikos

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all, copy_metadata


PROJECT_ROOT = Path(SPECPATH).parent.resolve()

# The frontend is mounted at runtime by FastAPI. ML libraries rely on dynamic
# imports and package data (yaml configs, tokenizer files), so collect_all is
# intentional for the release build. rapid_latex_ocr and the cn* packages ship
# configuration files their loaders read from inside the package directory.
# rapidocr is a transitive dependency of cnstd/cnocr (pix2text's detector and
# recognizer backends) and ships its own default_models.yaml the same way;
# missing it here caused a FileNotFoundError on first recognition in early builds.
datas = [(str(PROJECT_ROOT / "frontend"), "frontend")]
binaries = []
hiddenimports = ["pytesseract"]
# transformers and optimum expose their submodules through lazy loading
# (importlib at runtime, invisible to static analysis), so every submodule
# must be collected explicitly or the frozen app dies with
# "No module named 'transformers.models...'" when a model family is resolved.
for package_name in (
    "pix2tex",
    "pix2text",
    "rapid_latex_ocr",
    "cnstd",
    "cnocr",
    "rapidocr",
    "transformers",
    "optimum",
    "pypandoc",
    "pypdfium2",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

# The Tesseract program supplies Greek/English text recognition for "document"
# mode. Drop a platform build of it (plus leptonica) into packaging/vendor/
# tesseract/ and it is bundled here; otherwise the app still ships and simply
# reports that page-text recognition needs Tesseract installed. See
# docs/DESKTOP_PACKAGING.md. Nougat is never bundled (non-commercial weights).
# optimum (and transformers) decide which backends exist by probing package
# versions through importlib.metadata at import time. Without the dist-info
# records the frozen app would silently consider onnxruntime unavailable and
# fail to load the Pix2Text MFR engine.
for metadata_package in (
    "optimum",
    "transformers",
    "onnxruntime",
    "onnx",
    "torch",
    "tokenizers",
    "huggingface-hub",
    "numpy",
    "pillow",
):
    try:
        datas += copy_metadata(metadata_package)
    except Exception:
        pass  # not installed on this platform; the engine import guards handle it

vendor_tesseract = PROJECT_ROOT / "packaging" / "vendor" / "tesseract"
if vendor_tesseract.is_dir():
    datas.append((str(vendor_tesseract), "vendor/tesseract"))

# Several recognition packages run ``@torch.jit.script`` at import time, and
# TorchScript reads the original .py source through inspect.getsource(). By
# default PyInstaller ships bytecode only, which made the packaged app fail
# with "OSError: could not get source code" on the first recognition. Keeping
# the real source files for the whole recognition stack fixes that (PyInstaller
# does the same for torch itself in its bundled hook).
MODULE_COLLECTION_MODE = {
    # transformers' docstring decorators call inspect.getsource() on optimum's
    # classes while ``optimum.onnxruntime`` is imported (pix2text MFR path);
    # optimum has no PyInstaller hook, so its source must be kept explicitly.
    "optimum": "pyz+py",
    "timm": "pyz+py",            # jit-scripted activations, imported by pix2tex
    "cnstd": "pyz+py",           # yolov7.torch_utils is jit-scripted (detector)
    "cnocr": "pyz+py",
    "pix2tex": "pyz+py",
    "pix2text": "pyz+py",
    "x_transformers": "pyz+py",  # pix2tex decoder
    "einops": "pyz+py",          # torch-specific helpers are jit-compiled
    "rapidocr": "pyz+py",
    "rapid_latex_ocr": "pyz+py",
}

analysis = Analysis(
    [str(PROJECT_ROOT / "desktop" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    module_collection_mode=MODULE_COLLECTION_MODE,
    optimize=0,
)

pyz = PYZ(analysis.pure)

# App icon: the in-app brand mark (white ∫ on a green disc). Windows reads the
# .ico from the EXE; macOS reads the .icns from the BUNDLE below.
WINDOWS_ICON = PROJECT_ROOT / "packaging" / "MathOCR.ico"
MACOS_ICON = PROJECT_ROOT / "packaging" / "MathOCR.icns"
exe_icon = str(WINDOWS_ICON) if (sys.platform == "win32" and WINDOWS_ICON.is_file()) else None

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="MathOCR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=exe_icon,
)

collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MathOCR",
)

if sys.platform == "darwin":
    app = BUNDLE(
        collection,
        name="MathOCR.app",
        icon=str(MACOS_ICON) if MACOS_ICON.is_file() else None,
        bundle_identifier="com.christosbouronikos.mathocr",
        info_plist={
            "CFBundleDisplayName": "MathOCR",
            "CFBundleName": "MathOCR",
            "CFBundleShortVersionString": "1.0.6",
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "Copyright © 2026 Bouronikos Christos",
        },
    )
