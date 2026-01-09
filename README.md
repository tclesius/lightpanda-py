# lightpanda-py

Python bindings for [Lightpanda](https://github.com/lightpanda-io/browser), a fast headless browser for AI agents and web automation.

## Installation

```bash
pip install lightpanda-py
# or
uv add lightpanda-py
```

## Usage

### Quick fetch

```python
import lightpanda

response = lightpanda.fetch("https://example.com")
print(response.text)

# JSON APIs
response = lightpanda.fetch("https://httpbin.org/ip")
data = response.json()
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

## License

MIT
