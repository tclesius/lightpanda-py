import html
import json
import subprocess
from pathlib import Path
from typing import Literal, Any, IO
import os

__all__ = ["fetch", "serve", "mcp", "run", "version", "Response", "LightpandaError", "BINARY"]

os.environ.setdefault("LIGHTPANDA_DISABLE_TELEMETRY", "true")

BINARY = str(next((Path(__file__).parent / "bin").glob("lightpanda-*")))

LogLevel = Literal["debug", "info", "warn", "error", "fatal"]
DumpFormat = Literal[
    "html",
    "markdown",
    "pdf",
    "png",
    "semantic_tree",
    "semantic_tree_text",
    "structured_data",
]
StripMode = Literal["clutter", "css", "js", "invisible", "shell", "ui"]
WaitUntil = Literal[
    "load", "domcontentloaded", "networkalmostidle", "networkidle", "done"
]
Protocol = Literal["cdp", "webdriver"]


class LightpandaError(RuntimeError):
    """Raised when the Lightpanda binary exits with a non-zero status."""

    def __init__(self, returncode: int, stdout: bytes, stderr: str) -> None:
        super().__init__(f"lightpanda failed (exit code {returncode}): {stderr}")
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def build_cmd(*args, **options):
    cmd = [BINARY, *args]
    for key, value in options.items():
        flag = f"--{key.replace('_', '-')}"
        for item in value if isinstance(value, (list, tuple)) else [value]:
            if item is True:
                cmd.append(flag)
            elif item is not None and item is not False:
                cmd += [flag, str(item)]
    return cmd


def run_cmd(cmd: list[str], input: bytes | None = None) -> bytes:
    result = subprocess.run(cmd, input=input, capture_output=True)
    if result.returncode:
        raise LightpandaError(result.returncode, result.stdout, result.stderr.decode(errors="replace"))
    return result.stdout


class Response:
    def __init__(self, content: bytes) -> None:
        self.content = content

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    @property
    def html(self) -> str:
        return self.text

    def json(self):
        text = self.text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # JSON documents are rendered by the browser as <pre>{...}</pre>
            if "<pre>" not in text:
                raise
            return json.loads(html.unescape(text.split("<pre>")[1].split("</pre>")[0]))


def fetch(
    url: str | list[str],
    *,
    dump: DumpFormat = "html",
    strip_mode: StripMode | str | list[StripMode] | None = None,
    with_base: bool = False,
    with_frames: bool = False,
    dump_selector: str | None = None,
    dump_max_bytes: int | None = None,
    wait_ms: int | None = None,
    wait_until: WaitUntil | None = None,
    wait_selector: str | None = None,
    wait_script: str | None = None,
    inject_script: str | list[str] | None = None,
    terminate_ms: int | None = None,
    fail_on_http_error: bool = False,
    log_level: LogLevel = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
    **options: Any,
) -> Response:
    """
    Fetch a page with an ephemeral Lightpanda browser.

    Args:
        url: The URL to fetch, or a list of URLs (implies json=True; the output is {"results": [...]})
        dump: Output format - 'html', 'markdown', 'pdf', 'png', 'semantic_tree', 'semantic_tree_text'
            or 'structured_data' (default: "html")
        strip_mode: Tag groups to strip — 'clutter', 'css', 'js', 'invisible', 'shell', 'ui'.
            A comma-separated string or a list (optional)
        with_base: Add a <base> tag to the dump (default: False)
        with_frames: Include iframe contents (default: False)
        dump_selector: Dump only the first element matching this CSS selector (optional)
        dump_max_bytes: Soft cap on the dumped html or markdown, in bytes (optional)
        wait_ms: Wait time in milliseconds (default: 5000)
        wait_until: Wait until event — 'load', 'domcontentloaded', 'networkalmostidle', 'networkidle', 'done' (optional)
        wait_selector: Wait for an element matching this CSS selector to appear (optional)
        wait_script: Wait for this JavaScript expression to return truthy (optional)
        inject_script: JavaScript to run before any page script, a string or a list (optional)
        terminate_ms: Hard deadline in milliseconds after which JavaScript is terminated (optional)
        fail_on_http_error: Raise when the page's HTTP status is 400 or above (default: False)
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in milliseconds (optional)
        **options: Any other `lightpanda fetch` CLI option, e.g. json=True, user_agent="...",
            http_header=["X-A: 1", "X-B: 2"], cookie="cookies.json", obey_robots=True.
            Underscores become dashes, True adds a bare flag and lists repeat the flag.

    Returns:
        Response: A convenience wrapper around the raw output

    Raises:
        LightpandaError: If the browser exits with a non-zero status

    Example:
        >>> response = lightpanda.fetch("http://example.com")
        >>> response.text
    """
    urls = [url] if isinstance(url, str) else list(url)
    if len(urls) > 1:
        options.setdefault("json", True)
    cmd = build_cmd(
        "fetch",
        *urls,
        dump=dump,
        strip_mode=strip_mode,
        with_base=with_base,
        with_frames=with_frames,
        dump_selector=dump_selector,
        dump_max_bytes=dump_max_bytes,
        wait_ms=wait_ms,
        wait_until=wait_until,
        wait_selector=wait_selector,
        wait_script=wait_script,
        inject_script=inject_script,
        terminate_ms=terminate_ms,
        fail_on_http_error=fail_on_http_error,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
        **options,
    )
    return Response(run_cmd(cmd))


def serve(
    host: str = "127.0.0.1",
    port: int = 9222,
    advertise_host: str | None = None,
    *,
    cdp_max_connections: int | None = None,
    cdp_max_pending_connections: int | None = None,
    protocol: Protocol | list[Protocol] | None = None,
    unix_socket: str | None = None,
    remote_allow_origins: str | list[str] | None = None,
    log_level: LogLevel = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
    stdout: None | int | IO[Any] = None,
    stderr: None | int | IO[Any] = None,
    **options: Any,
) -> subprocess.Popen:
    """
    Start Lightpanda browser process with CDP server.

    Args:
        host: Host to bind the CDP server to (default: "127.0.0.1")
        port: Port to bind the CDP server to (default: 9222)
        advertise_host: Host to advertise in CDP responses, e.g. when host is 0.0.0.0 (optional)
        cdp_max_connections: Maximum simultaneous CDP connections (default: 16)
        cdp_max_pending_connections: Maximum pending connections in accept queue (default: 128)
        protocol: Automation protocol(s) to serve — 'cdp', 'webdriver' or both (default: "cdp")
        unix_socket: Listen on this absolute Unix-domain socket path instead of host/port (optional)
        remote_allow_origins: Origin(s) allowed in WebSocket upgrades, or "*" for any (optional)
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in milliseconds (optional)
        stdout: Standard output file handle (optional)
        stderr: Standard error file handle (optional)
        **options: Any other `lightpanda serve` CLI option, e.g. user_agent="...",
            block_urls=["*doubleclick*"], watchdog_ms=60000.
    Returns:
        subprocess.Popen: The process object for the Lightpanda browser

    Example:
        >>> proc = lightpanda.serve(host='127.0.0.1', port=9222)
        >>> # Do your magic ✨
        >>> proc.kill()
    """
    if "timeout" in options:
        raise TypeError(
            "serve() no longer accepts 'timeout': Lightpanda removed the --timeout option"
        )
    cmd = build_cmd(
        "serve",
        host=None if unix_socket else host,
        port=None if unix_socket else port,
        advertise_host=advertise_host,
        unix_socket=unix_socket,
        protocol=protocol,
        cdp_max_connections=cdp_max_connections,
        cdp_max_pending_connections=cdp_max_pending_connections,
        remote_allow_origins=remote_allow_origins,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
        **options,
    )
    proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
    print(f"🐼 Running Lightpanda's CDP server... {{ pid: {proc.pid} }}")
    return proc


def mcp(
    log_level: LogLevel = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    cdp_port: int | None = None,
    stdout: None | int | IO[Any] = None,
    stderr: None | int | IO[Any] = None,
    **options: Any,
) -> subprocess.Popen:
    """
    Start Lightpanda MCP (Model Context Protocol) server, over stdio by default or over HTTP when `port` is set.

    Args:
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in milliseconds (optional)
        host: Host to bind when `port` is set (default: "127.0.0.1")
        port: Serve MCP over HTTP on this port (POST JSON-RPC to /mcp) instead of stdio (optional)
        cdp_port: Also run a CDP server on this port, stdio mode only (optional)
        stdout: Standard output file handle, HTTP mode only; stdio mode always pipes stdin/stdout (optional)
        stderr: Standard error file handle (optional)
        **options: Any other `lightpanda mcp` CLI option, e.g. http_session_timeout=300.

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
        host=host,
        port=port,
        cdp_port=cdp_port,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
        **options,
    )
    if port is None:
        return subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr
        )
    return subprocess.Popen(cmd, stdout=stdout, stderr=stderr)


def run(script: str, *, log_level: LogLevel = "error", **options: Any) -> Response:
    """
    Run a PandaScript and return what it printed.

    Example:
        >>> response = lightpanda.run('''
        ...     const page = new Page();
        ...     await page.goto("https://example.com");
        ...     console.log(await page.evaluate("document.title"));
        ... ''')
        >>> response.text
    """
    return Response(run_cmd(build_cmd("run", "-", log_level=log_level, **options), script.encode()))


def version() -> str:
    """
    Return the Lightpanda binary version string.

    Example:
        >>> print(lightpanda.version())
    """
    return run_cmd(build_cmd("version")).decode().strip()
