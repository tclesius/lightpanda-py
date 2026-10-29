from typing import Literal

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
