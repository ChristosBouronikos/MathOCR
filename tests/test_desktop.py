"""Desktop-launcher tests by Bouronikos Christos <chrisbouronikos@gmail.com>.

Support MathOCR at https://paypal.me/christosbouronikos. These checks do not
open a GUI or load OCR models, so they are safe in local and GitHub CI runs.
"""

from urllib.parse import parse_qs, urlparse

from desktop import main as desktop_main
from desktop.main import desktop_url, find_available_port


def test_desktop_url_points_frontend_to_its_private_api() -> None:
    url = desktop_url(43210)
    parsed = urlparse(url)
    assert parsed.scheme == "http"
    assert parsed.netloc == "127.0.0.1:43210"
    assert parse_qs(parsed.query) == {
        "desktop": ["1"],
        "api": ["http://127.0.0.1:43210"],
    }


def test_find_available_port_returns_a_user_port(monkeypatch) -> None:
    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def bind(self, address):
            assert address == ("127.0.0.1", 0)

        def getsockname(self):
            return ("127.0.0.1", 43210)

    monkeypatch.setattr(desktop_main.socket, "socket", lambda *_args: FakeSocket())
    port = find_available_port()
    assert port == 43210
