import json
import subprocess
from pathlib import Path
from typing import Literal
import os

os.environ.setdefault("LIGHTPANDA_DISABLE_TELEMETRY", "true")

BINARY = str(list((Path(__file__).parent / "bin").glob("lightpanda-*"))[0])


def build_cmd(*args, **options):
    cmd = [BINARY, *args]
    for key, value in options.items():
        if value is None:
            continue
        elif value is True:
            cmd.append(f"--{key}")
        elif value is not False:
            cmd.extend([f"--{key}", str(value)])
    return cmd


class Response:
    def __init__(self, html: str) -> None:
        self.html = html

    @property
    def text(self):
        return self.html

    def json(self):
        return json.loads(self.html.split("<pre>")[1].split("</pre>")[0])


def serve(
    host: str = "127.0.0.1",
    port: int = 9222,
    timeout: int | None = 10,
    log_level: Literal["debug", "info", "warning", "error"] = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
) -> subprocess.Popen:
    """
    Start Lightpanda browser process with CDP server.

    Args:
        host: Host to bind the CDP server to (default: "127.0.0.1")
        port: Port to bind the CDP server to (default: 9222)
        timeout: Connection timeout in seconds (default: 10)
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in seconds (optional)

    Returns:
        subprocess.Popen: The process object for the Lightpanda browser

    Example:
        >>> proc = lightpanda.serve(host='127.0.0.1', port=9222)
        >>> # Do your magic ✨
        >>> proc.kill()
    """
    cmd = build_cmd(
        "serve",
        host=host,
        port=port,
        timeout=timeout,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
    )
    proc = subprocess.Popen(cmd)
    print(f"🐼 Running Lightpanda's CDP server... {{ pid: {proc.pid} }}")
    return proc


def fetch(
    url: str,
    *,
    with_base: bool = False,
    log_level: Literal["debug", "info", "warning", "error"] = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
) -> Response:
    """
    Fetch a page with an ephemeral Lightpanda browser.

    Args:
        url: The url to fetch
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in seconds (optional)

    Returns:
        Response: A convenience wrapper around the text response

    Example:
        >>> response = lightpanda.fetch("http://example.com")
        >>> json = response.json()
    """
    cmd = build_cmd(
        "fetch",
        url,
        dump=True,
        with_base=with_base,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"lightpanda failed: {result.stderr}")
    return Response(result.stdout)
