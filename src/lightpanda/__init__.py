import functools
import html
import json
import os
import subprocess
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Literal, ParamSpec, TypeVar

__all__ = ["BINARY", "CDP", "MCP", "Error", "Result", "agent", "fetch", "mcp", "run", "serve", "version"]

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
Provider = Literal[
    "anthropic",
    "openai",
    "gemini",
    "huggingface",
    "vercel",
    "mistral",
    "openrouter",
    "ollama",
    "llama_cpp",
    "vertex",
    "codex",
    "openai_compatible",
]
Effort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
SearchEngine = Literal["auto", "brave", "tavily", "exa", "keenable"]
Verbosity = Literal["low", "medium", "high"]


class Error(Exception):
    def __init__(self, message: str | bytes, code: int | None = None) -> None:
        if isinstance(message, bytes):
            message = message.decode(errors="replace").strip()
        super().__init__(message)
        self.code = code


P = ParamSpec("P")
R = TypeVar("R")


def reraise(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            raise Error(e.stderr, e.returncode) from e

    return wrapper


@dataclass
class Result:
    stdout: bytes
    stderr: bytes = b""

    def __str__(self) -> str:
        return self.text

    @property
    def text(self) -> str:
        return self.stdout.decode("utf-8", errors="replace").strip("\n")

    @property
    def bytes(self) -> bytes:
        return self.stdout

    def json(self):
        text = self.text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # JSON documents are rendered by the browser as <pre>{...}</pre>
            if "<pre>" not in text:
                raise
            return json.loads(html.unescape(text.split("<pre>")[1].split("</pre>")[0]))


class Server:
    def __init__(self, process: subprocess.Popen, endpoint: str | None = None) -> None:
        self.process = process
        self.endpoint = endpoint

    def stop(self, timeout: float = 5) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()


class CDP(Server):
    pass


class MCP(Server):
    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        message = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
        if self.endpoint:
            req = urllib.request.Request(self.endpoint, message, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                response = json.load(resp)
        else:
            assert self.process.stdin and self.process.stdout
            self.process.stdin.write(message + b"\n")
            self.process.stdin.flush()
            line = self.process.stdout.readline()
            if not line:
                raise Error("MCP server exited")
            response = json.loads(line)
        if "error" in response:
            raise Error(response["error"]["message"], response["error"]["code"])
        return response["result"]


@dataclass
class Option:
    flag: str
    value: Any

    def __iter__(self):
        values = self.value
        if not isinstance(values, (list, tuple)):
            values = [values]
        for value in values:
            if value is not None:
                yield from (self.flag, str(value))


@dataclass
class Flag:
    flag: str
    set: bool | None = True

    def __iter__(self):
        if self.set:
            yield self.flag


class Command:
    def __init__(self, binary: str, *args: str, **kwargs: Any) -> None:
        self.binary = binary
        self.args = args
        self.kwargs = kwargs

    @property
    def argv(self) -> list[str]:
        cmd = [self.binary, *self.args]
        for key, value in self.kwargs.items():
            flag = "--" + key.replace("_", "-")
            if isinstance(value, bool):
                cmd += Flag(flag, value)
            else:
                cmd += Option(flag, value)
        return cmd


@reraise
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
    **kwargs: Any,
) -> Result:
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
        **kwargs: Any other `lightpanda fetch` CLI option, e.g. json=True, user_agent="...",
            http_header=["X-A: 1", "X-B: 2"], cookie="cookies.json", obey_robots=True.
            Underscores become dashes, True adds a bare flag and lists repeat the flag.

    Returns:
        Result: The output; read it with .text, .bytes or .json()

    Raises:
        lightpanda.Error: If the browser exits with a non-zero status; .code is the exit status

    Example:
        >>> result = lightpanda.fetch("http://example.com")
        >>> result.text
    """
    urls = [url] if isinstance(url, str) else list(url)
    cmd = Command(
        BINARY,
        "fetch",
        *urls,
        json=kwargs.pop("json", len(urls) > 1),
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
        **kwargs,
    )
    proc = subprocess.run(cmd.argv, capture_output=True, check=True)
    return Result(proc.stdout, proc.stderr)


@reraise
def run(script: str, *, log_level: LogLevel = "error", **kwargs: Any) -> Result:
    """
    Run a PandaScript and return what it printed.

    Example:
        >>> result = lightpanda.run('''
        ...     const page = new Page();
        ...     await page.goto("https://example.com");
        ...     console.log(await page.evaluate("document.title"));
        ... ''')
        >>> result.text
    """
    cmd = Command(
        BINARY,
        "run",
        "-",
        log_level=log_level,
        **kwargs,
    )
    proc = subprocess.run(cmd.argv, input=script.encode(), capture_output=True, check=True)
    return Result(proc.stdout, proc.stderr)


@reraise
def agent(
    task: str,
    *,
    provider: Provider | None = None,
    model: str | None = None,
    base_url: str | None = None,
    url: str | None = None,
    attach: str | list[str] | None = None,
    effort: Effort | None = None,
    search_engine: SearchEngine | None = None,
    system_prompt: str | None = None,
    save: str | None = None,
    trace: str | None = None,
    trace_results: bool = False,
    verbosity: Verbosity | None = None,
    log_level: LogLevel = "error",
    **kwargs: Any,
) -> Result:
    """
    Let an AI agent browse to complete a task and return its answer.

    The API key is read from the environment, e.g. ANTHROPIC_API_KEY or OPENAI_API_KEY.

    Args:
        task: What the agent should do
        provider: AI provider, auto-detected from the API key in the environment (optional)
        model: Model name, defaults to a sensible one per provider (optional)
        base_url: Override the provider's API URL, e.g. for a local Ollama server (optional)
        url: Page to open before the first turn (optional)
        attach: File(s) to give the model along with the task, a path or a list (optional)
        effort: Reasoning effort — 'none', 'minimal', 'low', 'medium', 'high', 'xhigh' (default: "medium")
        search_engine: Web search API for the agent's search tool — 'auto', 'brave', 'tavily', 'exa', 'keenable' (default: "auto")
        system_prompt: Replace the default system prompt (optional)
        save: Write a replayable PandaScript to this path instead of answering (optional)
        trace: Write one JSON line per model and tool call to this path (optional)
        trace_results: Also write each tool result to the trace file (default: False)
        verbosity: Stderr chatter — 'low', 'medium', 'high' (optional)
        log_level: Logging level (default: "error")
        **kwargs: Any other `lightpanda agent` CLI option, e.g. obey_robots=True.

    Example:
        >>> result = lightpanda.agent("What is the top story?", url="https://news.ycombinator.com")
        >>> result.text
    """
    cmd = Command(
        BINARY,
        "agent",
        task=task,
        provider=provider,
        model=model,
        base_url=base_url,
        url=url,
        attach=attach,
        effort=effort,
        search_engine=search_engine,
        system_prompt=system_prompt,
        save=save,
        trace=trace,
        trace_results=trace_results,
        verbosity=verbosity,
        log_level=log_level,
        **kwargs,
    )
    proc = subprocess.run(cmd.argv, capture_output=True, check=True)
    return Result(proc.stdout, proc.stderr)


@reraise
def version(check: bool = False) -> Result:
    """
    Return the Lightpanda binary version.

    Args:
        check: Check whether a newer Lightpanda release is available and how to update (default: False)

    Returns:
        Result: The output; read it with .text

    Example:
        >>> print(lightpanda.version())
        >>> print(lightpanda.version(check=True))
    """
    cmd = Command(
        BINARY,
        "version",
        check=check,
    )
    proc = subprocess.run(cmd.argv, capture_output=True, check=True)
    return Result(proc.stdout, proc.stderr)


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
    **kwargs: Any,
) -> CDP:
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
        **kwargs: Any other `lightpanda serve` CLI option, e.g. user_agent="...",
            block_urls=["*doubleclick*"], watchdog_ms=60000.
    Returns:
        CDP: The running browser; connect to .endpoint, call .stop() or use it as a context manager

    Example:
        >>> with lightpanda.serve(host='127.0.0.1', port=9222) as cdp:
        ...     ...  # Do your magic ✨ with cdp.endpoint

        >>> cdp = lightpanda.serve(host='127.0.0.1', port=9222)
        >>> ...  # Do your magic ✨ with cdp.endpoint
        >>> cdp.stop()
    """
    cmd = Command(
        BINARY,
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
        **kwargs,
    )
    if unix_socket:
        return CDP(subprocess.Popen(cmd.argv, stdout=stdout, stderr=stderr))
    return CDP(subprocess.Popen(cmd.argv, stdout=stdout, stderr=stderr), f"http://{host}:{port}")


def mcp(
    log_level: LogLevel = "error",
    http_proxy: str | None = None,
    http_timeout: int | None = None,
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    cdp_port: int | None = None,
    stderr: None | int | IO[Any] = None,
    **kwargs: Any,
) -> MCP:
    """
    Start Lightpanda MCP (Model Context Protocol) server, over stdio by default or over HTTP when `port` is set.

    Args:
        log_level: Logging level (default: "error")
        http_proxy: HTTP proxy URL (optional)
        http_timeout: HTTP request timeout in milliseconds (optional)
        host: Host to bind when `port` is set (default: "127.0.0.1")
        port: Serve MCP over HTTP on this port (POST JSON-RPC to /mcp) instead of stdio (optional)
        cdp_port: Also run a CDP server on this port, stdio mode only (optional)
        stderr: Standard error file handle (optional)
        **kwargs: Any other `lightpanda mcp` CLI option, e.g. http_session_timeout=300.

    Returns:
        MCP: The running server; send JSON-RPC with .request(), call .stop() or use it as a context manager

    Example:
        >>> with lightpanda.mcp() as mcp:
        ...     print(mcp.request("tools/list"))

        >>> mcp = lightpanda.mcp()
        >>> print(mcp.request("tools/list"))
        >>> mcp.stop()
    """
    cmd = Command(
        BINARY,
        "mcp",
        host=host if port else None,
        port=port,
        cdp_port=cdp_port,
        log_level=log_level,
        http_proxy=http_proxy,
        http_timeout=http_timeout,
        **kwargs,
    )
    if not port:
        return MCP(subprocess.Popen(cmd.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr))
    return MCP(subprocess.Popen(cmd.argv, stderr=stderr), f"http://{host}:{port}/mcp")
