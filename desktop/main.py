"""Zero-install desktop launcher for MathOCR.

Created by Bouronikos Christos <chrisbouronikos@gmail.com>.
Support MathOCR at https://paypal.me/christosbouronikos.

PyInstaller freezes this module, Python, the OCR dependencies, and frontend
assets into a platform-specific application. At launch it starts the existing
FastAPI app on a private random loopback port and opens it in a native pywebview
window. The end user never needs to see Python, a terminal, or a browser tab.
"""

from __future__ import annotations

import multiprocessing
import os
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import uvicorn

from backend.app import app

HOST = "127.0.0.1"


def find_available_port(host: str = HOST) -> int:
    """Ask the operating system for an unused loopback TCP port."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((host, 0))
        return int(listener.getsockname()[1])


def desktop_url(port: int) -> str:
    """Build the UI URL and tell JavaScript which private API origin to use."""

    origin = f"http://{HOST}:{port}"
    query = urllib.parse.urlencode({"desktop": "1", "api": origin})
    return f"{origin}/?{query}"


def wait_until_ready(port: int, timeout: float = 30.0) -> None:
    """Wait for Uvicorn to accept requests before creating the native window."""

    health_url = f"http://{HOST}:{port}/api/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.1)
    raise RuntimeError("The local MathOCR engine did not start in time")


def run_headless() -> None:
    """Serve the API without a window (MATHOCR_HEADLESS=1).

    Used to smoke-test the frozen application: recognition can be exercised
    with plain HTTP requests, which catches packaging bugs (missing data
    files, missing sources for TorchScript) that only appear when frozen.
    """

    port = int(os.getenv("MATHOCR_PORT", "8765"))
    uvicorn.run(app, host=HOST, port=port, log_level="info")


def run_desktop() -> None:
    """Start the local service, show the window, and stop cleanly on exit."""

    # Imported lazily so unit tests and headless API use do not require GUI frameworks.
    import webview

    port = find_available_port()
    config = uvicorn.Config(
        app,
        host=HOST,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    server_thread = threading.Thread(target=server.run, name="mathocr-api", daemon=True)
    server_thread.start()

    try:
        wait_until_ready(port)
        webview.create_window(
            "MathOCR by Bouronikos Christos",
            desktop_url(port),
            width=1180,
            height=860,
            min_size=(760, 620),
            background_color="#f5f1e8",  # matches the interface's paper theme
            text_select=True,
        )
        webview.start(debug=os.getenv("MATHOCR_DESKTOP_DEBUG") == "1")
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


def main() -> None:
    """Freeze-safe console entry point used by PyInstaller."""

    multiprocessing.freeze_support()
    if os.getenv("MATHOCR_HEADLESS") == "1":
        run_headless()
    else:
        run_desktop()


if __name__ == "__main__":
    main()
