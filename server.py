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
)

mcp = FastMCP("Techla AI - Trợ lý")

# Core tools (always on)
company.register(mcp)
time_tool.register(mcp)
weather.register(mcp)
notes.register(mcp)
calc.register(mcp)

# Info tools (no auth)
news.register(mcp)
finance.register(mcp)
wiki.register(mcp)
translate.register(mcp)

# Personal data (local persistence)
reminder.register(mcp)
expense.register(mcp)

# Knowledge base search
kb_search.register(mcp)

# Optional: Home Assistant (only if configured)
if os.getenv("HA_URL") and os.getenv("HA_TOKEN"):
    home_assistant.register(mcp)

# Optional: Google Calendar (only if access token configured)
if os.getenv("GOOGLE_ACCESS_TOKEN"):
    calendar_gcal.register(mcp)


if __name__ == "__main__":
    mcp.run(transport="stdio")
