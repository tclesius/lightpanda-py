#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["lightpanda-py>=0.4.0"]
# ///
"""Scrape the Hacker News front page into a list of stories."""

import json

import lightpanda

SCRIPT = """
const page = new Page();
await page.goto("https://news.ycombinator.com");

const stories = await page.evaluate(`
  const stories = [];

  for (const row of document.querySelectorAll("tr.athing")) {
    const link = row.querySelector(".titleline > a");
    const score = row.nextElementSibling.querySelector(".score");

    stories.push({
      title: link.textContent,
      url: link.href,
      points: score ? parseInt(score.textContent) : 0,
    });
  }

  stories;
`);

console.log(stories);
"""

stories = json.loads(lightpanda.run(SCRIPT).text)
stories.sort(key=lambda story: story["points"], reverse=True)

for story in stories[:10]:
    print(f"{story['points']:>5}  {story['title']}")
    print(f"       {story['url']}")
