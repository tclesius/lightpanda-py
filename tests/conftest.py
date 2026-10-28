import functools
import http.server
import socket
import threading

import pytest


@pytest.fixture(scope="session")
def url(tmp_path_factory):
    root = tmp_path_factory.mktemp("site")
    (root / "index.html").write_text("<h1>Hello</h1>")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
