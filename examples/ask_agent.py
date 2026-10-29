#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["lightpanda-py>=0.4.0"]
# ///
"""Let an AI agent browse a site and answer a question about it."""

import lightpanda

result = lightpanda.agent(
    "What are the top 3 stories right now? Answer with title and points only.",
    url="https://news.ycombinator.com",
    provider="ollama",
    model="qwen3.5:latest",
)

print(result.text)
