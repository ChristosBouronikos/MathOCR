"""One-command launcher for running MathOCR from source.

Created by Bouronikos Christos <chrisbouronikos@gmail.com>.
Support MathOCR at https://paypal.me/christosbouronikos.

End users do NOT need this: the packaged desktop application (MathOCR.app /
MathOCR-Setup.exe) bundles Python, every library, and Pandoc. This script is
the convenience path for people running the source checkout. The ``run.command``
(macOS) and ``run.bat`` (Windows) wrappers make sure Python itself exists and
then hand over to this file, which:

1. creates a local virtual environment on first run,
2. installs the dependencies into it,
3. re-launches itself with that environment's Python, and
4. starts the local service and opens MathOCR in the browser.

Run it directly with any Python 3.10+::

    python scripts/launch.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
STAMP = VENV_DIR / ".mathocr-deps-installed"
HOST = "127.0.0.1"
PORT = 8000


def venv_python() -> Path:
    """Path to the interpreter inside the local virtual environment."""

    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def running_inside_venv() -> bool:
    try:
        return Path(sys.executable).resolve() == venv_python().resolve()
    except OSError:
        return False


def ensure_environment() -> None:
    """Create the virtual environment and install dependencies once."""

    if not venv_python().exists():
        print("Creating a local Python environment in .venv …")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    if not STAMP.exists():
        print("Installing MathOCR dependencies (first run only, a few minutes) …")
        python = str(venv_python())
        subprocess.check_call([python, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call(
            [python, "-m", "pip", "install", "-r", str(ROOT / "backend" / "requirements.txt")]
        )
        STAMP.write_text("ok\n", encoding="utf-8")


def relaunch_in_venv() -> None:
    """Re-run this script using the virtual environment's interpreter."""

    os.execv(str(venv_python()), [str(venv_python()), str(Path(__file__).resolve()), *sys.argv[1:]])


def serve() -> None:
    """Start Uvicorn and open the interface in the default browser."""

    import threading

    import uvicorn

    url = f"http://{HOST}:{PORT}"
    print(f"\nMathOCR is starting at {url}")
    print("Close this window (or press Ctrl+C) to stop the local engine.\n")
    threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    uvicorn.run("backend.app:app", host=HOST, port=PORT, log_level="warning")


def main() -> None:
    if not running_inside_venv():
        ensure_environment()
        relaunch_in_venv()
        return
    os.chdir(ROOT)  # imports and the frontend mount are resolved from the root
    serve()


if __name__ == "__main__":
    main()
