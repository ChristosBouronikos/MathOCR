"""Build a platform-native MathOCR application with PyInstaller.

Created by Bouronikos Christos <chrisbouronikos@gmail.com>.
Support MathOCR at https://paypal.me/christosbouronikos.

Run this script from the repository root after installing
``backend/requirements-desktop.txt``. PyInstaller must run on each target OS;
this script validates the expected output so CI fails with a useful message.
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# Keep PyInstaller's architecture-specific binary cache inside the project. This
# avoids permission problems in sandboxed CI/build environments and is ignored.
os.environ.setdefault("PYINSTALLER_CONFIG_DIR", str(ROOT / ".pyinstaller-cache"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".build-cache" / "matplotlib"))

import PyInstaller.__main__  # noqa: E402  (environment must be configured first)


def expected_application() -> Path:
    """Return the primary executable or application bundle for this OS."""

    if sys.platform == "darwin":
        return DIST / "MathOCR.app"
    executable = "MathOCR.exe" if sys.platform == "win32" else "MathOCR"
    return DIST / "MathOCR" / executable


def validate_bundled_resources(output: Path) -> None:
    """Fail a Windows release build if RapidOCR's manifest was omitted."""

    if sys.platform != "win32":
        return

    manifest = output.parent / "_internal" / "rapidocr" / "default_models.yaml"
    if not manifest.is_file():
        raise SystemExit(
            "PyInstaller omitted RapidOCR's model manifest: " f"{manifest}"
        )


def main() -> None:
    """Clean stale output, run the specification, and validate the artifact."""

    for directory in (DIST, ROOT / "build"):
        if directory.exists():
            shutil.rmtree(directory)

    print(f"Building MathOCR for {platform.system()} {platform.machine()}")
    PyInstaller.__main__.run(
        [
            "--noconfirm",
            "--clean",
            "--distpath",
            str(DIST),
            "--workpath",
            str(ROOT / "build"),
            str(ROOT / "packaging" / "MathOCR.spec"),
        ]
    )
    output = expected_application()
    if not output.exists():
        raise SystemExit(f"PyInstaller finished without creating {output}")
    validate_bundled_resources(output)
    print(f"Desktop application created: {output}")


if __name__ == "__main__":
    main()
