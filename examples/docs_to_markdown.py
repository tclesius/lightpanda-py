#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["lightpanda-py>=0.4.0"]
# ///
"""Fetch several pages as clean Markdown, e.g. to feed an LLM or a RAG index."""

from pathlib import Path
from urllib.parse import urlparse

import lightpanda

URLS = [
    "https://docs.python.org/3/tutorial/introduction.html",
    "https://docs.python.org/3/tutorial/controlflow.html",
    "https://docs.python.org/3/tutorial/datastructures.html",
]

OUTPUT_DIR = Path("markdown")
MAX_BYTES = 20_000


def markdown_path(url):
    name = Path(urlparse(url).path).stem
    return OUTPUT_DIR / f"{name}.md"


OUTPUT_DIR.mkdir(exist_ok=True)

result = lightpanda.fetch(URLS, dump="markdown", strip_mode="clutter", dump_max_bytes=MAX_BYTES)
pages = result.json()["results"]

for page in pages:
    if page["http_status"] != 200:
        print(f"Skipped {page['url']} (HTTP {page['http_status']})")
        continue

    path = markdown_path(page["url"])
    path.write_text(page["content"])
    print(f"Saved {page['url']} to {path}")
