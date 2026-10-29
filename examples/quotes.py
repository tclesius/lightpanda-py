#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["lightpanda-py>=0.4.0", "playwright"]
# ///
"""Click through a JavaScript-rendered, paginated site with Playwright and save it as JSON."""

import json

from playwright.sync_api import sync_playwright

import lightpanda

quotes = []

with lightpanda.serve() as cdp, sync_playwright() as playwright:
    browser = playwright.chromium.connect_over_cdp(cdp.endpoint)
    page = browser.new_page()
    page.goto("https://quotes.toscrape.com/js/")

    while True:
        for quote in page.locator(".quote").all():
            quotes.append({
                "text": quote.locator(".text").inner_text(),
                "author": quote.locator(".author").inner_text(),
                "tags": quote.locator(".tag").all_inner_texts(),
            })

        next_link = page.locator("li.next > a")
        if next_link.count() == 0:
            break

        next_link.click()
        page.wait_for_load_state()

with open("quotes.json", "w") as f:
    json.dump(quotes, f, indent=2, ensure_ascii=False)

print(f"Saved {len(quotes)} quotes to quotes.json")
