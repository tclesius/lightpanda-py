# lightpanda-py

Embedded [Lightpanda](https://github.com/lightpanda-io/browser) for Python, a fast headless browser for AI agents and web automation.

## Installation

```bash
pip install lightpanda-py
# or
uv add lightpanda-py
```

No extra setup — the Lightpanda binary is bundled in the package.

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
response = lightpanda.fetch("https://example.com", strip_mode="js,css")

# Wait for network idle before dump
response = lightpanda.fetch("https://example.com", wait_until="networkidle")
```

### CDP Server

Start a CDP server to use with Playwright, Puppeteer, or any CDP client:

```python
import lightpanda

proc = lightpanda.serve(host="127.0.0.1", port=9222)
# 🐼 Running Lightpanda's CDP server... { pid: 12345 }

# Connect with your favorite CDP client...

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

### Version

```python
import lightpanda

print(lightpanda.version())
```

## License

MIT
