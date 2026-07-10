# MathOCR desktop packaging

Prepared by **Bouronikos Christos** ([chrisbouronikos@gmail.com](mailto:chrisbouronikos@gmail.com)). If this work is useful, please [support MathOCR on PayPal](https://paypal.me/christosbouronikos).

The desktop edition packages the existing frontend and Python service into an application that requires no Python, command line, Pandoc, or library installation from the end user.

## Runtime design

`desktop/main.py` starts FastAPI on a random `127.0.0.1` port, waits for its health endpoint, and opens that origin in a pywebview native window. Closing the window stops the server. The service is never bound to a public network interface.

PyInstaller produces a one-folder application because large machine-learning runtimes start more reliably from installed files than from a self-extracting `--onefile` executable. The folder is hidden inside `MathOCR.app` on macOS and installed under Program Files by Inno Setup on Windows.

The `pypandoc_binary` build dependency supplies Pandoc inside the application. `backend.app.find_pandoc()` checks the frozen package before looking at the user's `PATH`.

## Bundling Tesseract (optional but recommended)

Greek/English page-text recognition in **document** mode uses the Tesseract program. `pytesseract` (the Python binding) is bundled automatically, but the Tesseract executable is a native binary that must be supplied per platform. Two supported options:

1. **Bundle it.** Place a platform build of Tesseract (the executable plus its shared libraries — leptonica, image codecs) under `packaging/vendor/tesseract/`. The PyInstaller spec copies that folder into the app, and `backend.engines.find_tesseract_binary()` finds it via `MEIPASS/vendor/tesseract/`. The Greek/English `traineddata` is downloaded on demand into the model store, so it need not be bundled.
2. **Skip it.** If `packaging/vendor/tesseract/` is absent, the app still ships. Math recognition works fully; document mode returns the equations and reports that page-text recognition needs Tesseract installed. This is acceptable for a first release.

Nougat is **never** bundled — its weights are non-commercial. It stays an opt-in `pip install nougat-ocr` for the source workflow.

## First-launch model behavior

The installer contains the OCR libraries but not their downloadable weights. On the first recognition (or when the user presses **Download all models now**), MathOCR fetches the weights into a single per-user folder:

- macOS: `~/Library/Application Support/MathOCR/models`
- Windows: `%LOCALAPPDATA%\MathOCR\models`

Everything (Pix2Text, pix2tex, RapidLaTeXOCR checkpoints, Tesseract language data) lives under that one root — see `backend/model_store.py`. That single location is what lets the in-app storage panel report true sizes and delete a model to reclaim disk space; it re-downloads automatically when next needed. Subsequent runs reuse the cache and work offline. Total download is about **480 MB** (plus ~1.4 GB only if the user opts into Nougat).

## Local developer build

Build on the operating system being targeted. Python 3.11 is recommended.

```bash
python3.11 -m venv .venv-desktop
source .venv-desktop/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements-desktop.txt
python scripts/build_desktop.py
```

On macOS, create the disk image:

```bash
bash scripts/package_macos.sh
```

On Windows, install Inno Setup 6 and run:

```powershell
.\scripts\package_windows.ps1
```

Expected outputs are:

- `dist/MathOCR-macOS-<architecture>.dmg`
- `dist/MathOCR-Setup.exe`

## GitHub builds

Run **Build MathOCR desktop installers** under GitHub Actions, or push a version tag such as `v0.1.0`. The workflow builds independently on macOS and Windows and publishes downloadable workflow artifacts.

## Signing requirements

Unsigned development artifacts are suitable for internal testing, but operating systems may display security warnings.

For public macOS distribution, sign all executable code with an Apple Developer ID, enable hardened runtime, notarize the final disk image, and staple its ticket. This requires credentials owned by the publisher and should be added as protected GitHub secrets.

For public Windows distribution, use an Authenticode code-signing certificate and sign both `MathOCR.exe` and `MathOCR-Setup.exe`. Signing credentials must never be committed to this repository.

## Release checklist

1. Run API, export, and launcher tests.
2. Build on each native target architecture.
3. Test on a clean computer without Python or Pandoc installed.
4. Verify first-run model download, offline second run, PDF limits, and Word export.
5. Include third-party license notices for every redistributed binary and model.
6. Sign, notarize where applicable, and malware-scan the final installer.
7. Publish SHA-256 checksums alongside the release.

