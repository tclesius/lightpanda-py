# lightpanda-py

<img width="200" alt="panda" src="https://github.com/user-attachments/assets/9564d2f1-5096-4dc3-9c13-384b8c6e5818" />

[Lightpanda](https://github.com/lightpanda-io/browser) for Python, a fast headless browser for AI agents and web automation. Zero dependencies, browser included.

### Installation

```bash
pip install lightpanda-py
```

### Example usage

```python
import lightpanda

result = lightpanda.fetch("https://example.com", dump="markdown")
print(result.text)
```

### Output formats

```python
import lightpanda

html = lightpanda.fetch("https://example.com").text
markdown = lightpanda.fetch("https://example.com", dump="markdown").text
data = lightpanda.fetch("https://httpbin.org/ip").json()

# JSON-LD, OpenGraph, Twitter card and meta tags
meta = lightpanda.fetch("https://example.com", dump="structured_data").json()

# Text-only rendering as PNG or PDF
png = lightpanda.fetch("https://example.com", dump="png").bytes
```

### Waiting and stripping

```python
import lightpanda

# Wait for network idle, or for an element to appear
lightpanda.fetch("https://example.com", wait_until="networkidle")
lightpanda.fetch("https://example.com", wait_selector="h1", dump_selector="h1")

# Drop scripts and styles, or keep only the main content
lightpanda.fetch("https://example.com", strip_mode=["js", "css"])
lightpanda.fetch("https://example.com", dump="markdown", strip_mode="clutter")
```

### Status and multiple URLs

`json=True` adds the HTTP status, headers and page diagnostics:

```python
import lightpanda

status = lightpanda.fetch("https://example.com", dump="markdown", json=True).json()
print(status["http_status"], status["content"])

results = lightpanda.fetch(["https://example.com", "https://example.org"], dump="markdown").json()
for result in results["results"]:
    print(result["url"], result["http_status"])
```

### Any CLI flag

Underscores become dashes, `True` adds a bare flag, and lists repeat the flag:

```python
import lightpanda

result = lightpanda.fetch(
    "https://example.com",
    http_header=["Authorization: Bearer token"],  # --http-header ...
    user_agent_suffix="my-crawler",               # --user-agent-suffix my-crawler
    obey_robots=True,                             # --obey-robots
    cookie_jar="cookies.json",                    # --cookie-jar cookies.json
)
```

Errors raise `lightpanda.Error`; its message is the browser's stderr and `.code` the exit status. Pass `fail_on_http_error=True` to also raise on HTTP 4xx/5xx.

### Using Playwright or Puppeteer

```python
import lightpanda
from playwright.sync_api import sync_playwright

with lightpanda.serve(host="127.0.0.1", port=9222) as cdp, sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(cdp.endpoint)
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.content())
    browser.close()
```

```python
import lightpanda

# Write logs to files
server = lightpanda.serve(stdout=open("lightpanda.out.log", "w"), stderr=open("lightpanda.err.log", "w"))

# CDP on / and WebDriver BiDi on /session, same port
server = lightpanda.serve(protocol=["cdp", "webdriver"])

# CDP over a Unix-domain socket instead of TCP
server = lightpanda.serve(unix_socket="/tmp/lightpanda.sock")
```

### Running an MCP server

```python
import lightpanda

with lightpanda.mcp() as mcp:
    print(mcp.request("tools/list"))  # list of available tools

# Or over HTTP, clients POST JSON-RPC to mcp.endpoint (http://127.0.0.1:8080/mcp)
with lightpanda.mcp(port=8080) as mcp:
    ...
```

### Running tests

The bundled browser version is pinned in `.browser-version`. Download it for your platform, then run pytest:

```bash
scripts/get-browser lightpanda-x86_64-linux
uv run pytest
```

Available platforms:

- `lightpanda-aarch64-macos` - macOS arm64 (default)
- `lightpanda-x86_64-macos` - macOS x86_64
- `lightpanda-aarch64-linux` - Linux arm64
- `lightpanda-x86_64-linux` - Linux x86_64

### License

MIT
