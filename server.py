"""Techla AI MCP server — stdio entry point.

Run via mcp_pipe.py bridge to Xiaozhi cloud, or directly for local MCP clients.
"""
import os
import sys
from pathlib import Path

# Load .env if present (no external dep — simple parser)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value

from mcp.server.fastmcp import FastMCP

from tools import (
    company,
    time_tool,
    weather,
    notes,
    calc,
    news,
    finance,
    wiki,
    translate,
    reminder,
    expense,
    kb_search,
    home_assistant,
    calendar_gcal,
    web_search,
    apify_scraper,
    memory_kg,
    notion_workspace,
    github_repo,
    slack_chat,
    file_ops,
    url_fetch,
    database,
    telegram_bot,
    pc_control,
    browser_playwright,
)

mcp = FastMCP("Techla AI - Trợ lý")

# === Core tools (always on, no auth) ===
company.register(mcp)
time_tool.register(mcp)
weather.register(mcp)
notes.register(mcp)
calc.register(mcp)
news.register(mcp)
finance.register(mcp)
wiki.register(mcp)
translate.register(mcp)
reminder.register(mcp)
expense.register(mcp)
kb_search.register(mcp)
memory_kg.register(mcp)       # local JSON, no auth
file_ops.register(mcp)        # local files, no auth
url_fetch.register(mcp)       # plain HTTP, no auth
database.register(mcp)        # local SQLite default

# === Conditional integrations (env-gated) ===
if os.getenv("HA_URL") and os.getenv("HA_TOKEN"):
    home_assistant.register(mcp)

if os.getenv("GOOGLE_ACCESS_TOKEN"):
    calendar_gcal.register(mcp)

if os.getenv("BRAVE_API_KEY"):
    web_search.register(mcp)

if os.getenv("APIFY_TOKEN"):
    apify_scraper.register(mcp)

if os.getenv("NOTION_TOKEN"):
    notion_workspace.register(mcp)

if os.getenv("GITHUB_TOKEN"):
    github_repo.register(mcp)

if os.getenv("SLACK_BOT_TOKEN"):
    slack_chat.register(mcp)

if os.getenv("TELEGRAM_BOT_TOKEN"):
    telegram_bot.register(mcp)

if os.getenv("ENABLE_PC_CONTROL", "").lower() in ("1", "true", "yes"):
    pc_control.register(mcp)

if os.getenv("ENABLE_BROWSER_PLAYWRIGHT", "").lower() in ("1", "true", "yes"):
    browser_playwright.register(mcp)


if __name__ == "__main__":
    mcp.run(transport="stdio")
