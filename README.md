# lightpanda-py

Embedded [Lightpanda](https://github.com/lightpanda-io/browser) for Python, a fast headless browser for AI agents and web automation.

## Installation

```bash
pip install lightpanda-py
# or
uv add lightpanda-py
```

No extra setup - the Lightpanda binary is bundled in the package.

## Usage

### Fetch

Spin up an ephemeral browser to fetch a page:

```python
import lightpanda

response = lightpanda.fetch("https://example.com")
print(response.text)

# JSON APIs
response = lightpanda.fetch("https://httpbin.org/ip")
data = response.json()

# Markdown output
response = lightpanda.fetch("https://example.com", dump="markdown")

# Strip JS/CSS from output
response = lightpanda.fetch("https://example.com", strip_mode=["js", "css"])

# Keep only the main content, like a reader mode
response = lightpanda.fetch("https://example.com", dump="markdown", strip_mode="clutter")

# Wait for network idle before dump
response = lightpanda.fetch("https://example.com", wait_until="networkidle")

# Wait for an element, then dump only that element
response = lightpanda.fetch("https://example.com", wait_selector="h1", dump_selector="h1")

# JSON-LD, OpenGraph, Twitter card and meta tags
data = lightpanda.fetch("https://example.com", dump="structured_data").json()

# Text-only rendering as PNG or PDF (raw bytes)
png = lightpanda.fetch("https://example.com", dump="png").content
```

Get the HTTP status, headers and page diagnostics along with the dump, or fetch several URLs at once:

```python
import lightpanda

status = lightpanda.fetch("https://example.com", dump="markdown", json=True).json()
print(status["http_status"], status["content"])

results = lightpanda.fetch(["https://example.com", "https://example.org"], dump="markdown").json()
for result in results["results"]:
    print(result["url"], result["http_status"])
```

Every other `lightpanda` CLI option can be passed as a keyword argument. Underscores become dashes, `True` adds a bare flag and lists repeat the flag:

```python
import lightpanda

response = lightpanda.fetch(
    "https://example.com",
    http_header=["Authorization: Bearer token"],  # --http-header ...
    user_agent_suffix="my-crawler",               # --user-agent-suffix my-crawler
    obey_robots=True,                             # --obey-robots
    cookie_jar="cookies.json",                    # --cookie-jar cookies.json
)
```

A non-zero exit of the browser raises `lightpanda.LightpandaError` (a `RuntimeError`) with `returncode`, `stdout` and `stderr`. Pass `fail_on_http_error=True` to also raise on HTTP 4xx/5xx responses.

### CDP Server

Start a CDP server to use with Playwright, Puppeteer, or any CDP client:

```python
import lightpanda

proc = lightpanda.serve(host="127.0.0.1", port=9222)
# 🐼 Running Lightpanda's CDP server... { pid: 12345 }

# Connect with your favorite CDP client...

proc.kill()
```

Write browser logs to files:

```python
import lightpanda

stdout = open("lightpanda.out.log", "w")
stderr = open("lightpanda.err.log", "w")

proc = lightpanda.serve(stdout=stdout, stderr=stderr)

proc.kill()
```

With Playwright:

```python
import lightpanda
from playwright.sync_api import sync_playwright

proc = lightpanda.serve()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.content())
    browser.close()

proc.kill()
```

Serve WebDriver BiDi next to CDP, or listen on a Unix socket:

```python
import lightpanda

# CDP on / and WebDriver BiDi on /session, same port
proc = lightpanda.serve(protocol=["cdp", "webdriver"])
proc.kill()

# CDP over a Unix-domain socket instead of TCP
proc = lightpanda.serve(unix_socket="/tmp/lightpanda.sock")
proc.kill()
```

### MCP Server

Start a [Model Context Protocol](https://modelcontextprotocol.io) server over stdio:

```python
import lightpanda, json

proc = lightpanda.mcp()

proc.stdin.write(b'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n')
proc.stdin.flush()
print(json.loads(proc.stdout.readline()))  # list of available tools

proc.kill()
```

Or serve MCP over HTTP (clients `POST` JSON-RPC to `/mcp`):

```python
import lightpanda

proc = lightpanda.mcp(port=8080)

proc.kill()
```

### Version

```python
import lightpanda

print(lightpanda.version())
```

## Development

The bundled Lightpanda browser version is pinned in `.browser-version`.

Download the pinned browser for local development:

```bash
scripts/get-browser
```

By default this downloads the macOS arm64 binary. To use another asset or browser version:

```bash
scripts/get-browser lightpanda-x86_64-linux
scripts/get-browser lightpanda-aarch64-macos 1.0.1
```

Available raw browser assets:

- `lightpanda-aarch64-macos` - macOS arm64
- `lightpanda-x86_64-macos` - macOS x86_64
- `lightpanda-aarch64-linux` - Linux arm64
- `lightpanda-x86_64-linux` - Linux x86_64

### Tests

The integration tests run the real browser against a local HTTP server, so download the browser for your platform first:

```bash
scripts/get-browser lightpanda-x86_64-linux
```

```bash
uv run pytest
```

## License

MIT
