# -*- mode: python ; coding: utf-8 -*-
# MathOCR PyInstaller recipe by Bouronikos Christos <chrisbouronikos@gmail.com>.
# Support development: https://paypal.me/christosbouronikos

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_all


PROJECT_ROOT = Path(SPECPATH).parent.resolve()

# The frontend is mounted at runtime by FastAPI. ML libraries rely on dynamic
# imports and package data (yaml configs, tokenizer files), so collect_all is
# intentional for the release build. rapid_latex_ocr and the cn* packages ship
# configuration files their loaders read from inside the package directory.
datas = [(str(PROJECT_ROOT / "frontend"), "frontend")]
binaries = []
hiddenimports = ["pytesseract"]
for package_name in (
    "pix2tex",
    "pix2text",
    "rapid_latex_ocr",
    "cnstd",
    "cnocr",
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
vendor_tesseract = PROJECT_ROOT / "packaging" / "vendor" / "tesseract"
if vendor_tesseract.is_dir():
    datas.append((str(vendor_tesseract), "vendor/tesseract"))

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
    optimize=0,
)

pyz = PYZ(analysis.pure)

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
        bundle_identifier="com.christosbouronikos.mathocr",
        info_plist={
            "CFBundleDisplayName": "MathOCR",
            "CFBundleName": "MathOCR",
            "CFBundleShortVersionString": "1.0.1",
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "Copyright © 2026 Bouronikos Christos",
        },
    )
