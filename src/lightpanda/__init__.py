import json
import subprocess
from pathlib import Path
from typing import Literal, Any, IO
import os

__all__ = ["fetch", "serve", "mcp", "version", "BINARY"]

os.environ.setdefault("LIGHTPANDA_DISABLE_TELEMETRY", "true")

BINARY = str(next((Path(__file__).parent / "bin").glob("lightpanda-*")))


def build_cmd(*args, **options):
    cmd = [BINARY, *args]
    for key, value in options.items():
        if value is None:
            continue
        flag = f"--{key.replace('_', '-')}"
        if value is True:
            cmd.append(flag)
        elif value is not False:
            cmd.extend([flag, str(value)])
    return cmd


class Response:
    def __init__(self, html: str) -> None:
        self.html = html

    @property
    def text(self):
        return self.html

    def json(self):
        return json.loads(self.html.split("<pre>")[1].split("</pre>")[0])


def fetch(
    url: str,
    *,
    dump: Literal["html", "markdown", "semantic_tree", "semantic_tree_text"] = "html",
    strip_mode: str | None = None,
    with_base: bool = False,
    with_frames: bool = False,
    wait_ms: int | None = None,
    wait_until: Literal["load", "domcontentloaded", "networkidle", "done"]
    | None = None,
    log_level: Literal["debug", "info", "warning", "error"] = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
) -> Response:
    """
    Fetch a page with an ephemeral Lightpanda browser.

    Args:
        url: The URL to fetch
        dump: Output format - 'html', 'markdown', 'semantic_tree', or 'semantic_tree_text' (default: "html")
        strip_mode: Comma-separated tag groups to strip — 'js', 'css', 'ui', 'full' (optional)
        with_base: Add a <base> tag to the dump (default: False)
        with_frames: Include iframe contents (default: False)
        wait_ms: Wait time in milliseconds (default: 5000)
        wait_until: Wait until event — 'load', 'domcontentloaded', 'networkidle', 'done' (optional)
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in seconds (optional)

    Returns:
        Response: A convenience wrapper around the text response

    Example:
        >>> response = lightpanda.fetch("http://example.com")
        >>> response.text
    """
    cmd = build_cmd(
        "fetch",
        url,
        dump=dump,
        strip_mode=strip_mode,
        with_base=with_base,
        with_frames=with_frames,
        wait_ms=wait_ms,
        wait_until=wait_until,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"lightpanda failed: {result.stderr}")
    return Response(result.stdout)


def serve(
    host: str = "127.0.0.1",
    port: int = 9222,
    advertise_host: str | None = None,
    timeout: int | None = 10,
    cdp_max_connections: int | None = None,
    cdp_max_pending_connections: int | None = None,
    log_level: Literal["debug", "info", "warning", "error"] = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
    stdout: None | int | IO[Any] = None,
    stderr: None | int | IO[Any] = None,
) -> subprocess.Popen:
    """
    Start Lightpanda browser process with CDP server.

    Args:
        host: Host to bind the CDP server to (default: "127.0.0.1")
        port: Port to bind the CDP server to (default: 9222)
        advertise_host: Host to advertise in CDP responses, e.g. when host is 0.0.0.0 (optional)
        timeout: Inactivity timeout in seconds before disconnecting clients (default: 10)
        cdp_max_connections: Maximum simultaneous CDP connections (default: 16)
        cdp_max_pending_connections: Maximum pending connections in accept queue (default: 128)
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in seconds (optional)
        stdout: Standard output file handle (optional)
        stderr: Standard error file handle (optional)
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
        advertise_host=advertise_host,
        timeout=timeout,
        cdp_max_connections=cdp_max_connections,
        cdp_max_pending_connections=cdp_max_pending_connections,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
    )
    proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
    print(f"🐼 Running Lightpanda's CDP server... {{ pid: {proc.pid} }}")
    return proc


def mcp(
    log_level: Literal["debug", "info", "warning", "error"] = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
) -> subprocess.Popen:
    """
    Start Lightpanda MCP (Model Context Protocol) server over stdio.

    Args:
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in seconds (optional)

    Returns:
        subprocess.Popen: The process object for the MCP server

    Example:
        >>> import json
        >>> proc = lightpanda.mcp()
        >>> proc.stdin.write(b'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\\n')
        >>> proc.stdin.flush()
        >>> print(json.loads(proc.stdout.readline()))
        >>> proc.kill()
    """
    cmd = build_cmd(
        "mcp",
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
    )
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def version() -> str:
    """
    Return the Lightpanda binary version string.

    Example:
        >>> print(lightpanda.version())
    """
    cmd = build_cmd("version")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"lightpanda failed: {result.stderr}")
    return result.stdout.strip()
