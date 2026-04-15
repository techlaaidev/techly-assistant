# Codebase Summary — Techly Assistant

## Entry points

| File | Role |
|---|---|
| `mcp_pipe.py` | Bridge WebSocket ↔ stdio. Spawns `server.py` as subprocess, forwards JSON-RPC giữa Xiaozhi cloud và MCP server. Intercept `ping` tại bridge (respond ngay, không xuống server). |
| `server.py` | FastMCP server. Load `.env`, register tools conditionally theo env gate. Run stdio transport. |

## tools/ — 27 modules, 85 tools

### Always-on (16 modules, 39 tools)

| Module | N | Purpose |
|---|---|---|
| `company.py` | 6 | Đọc section từ `company_data.md` — doanh thu, đơn, KH VIP, sản phẩm, lịch họp, info |
| `time_tool.py` | 1 | Datetime hiện tại tiếng Việt |
| `weather.py` | 1 | open-meteo API, không cần key |
| `notes.py` | 3 | CRUD `data/notes.txt` |
| `calc.py` | 1 | Safe eval whitelist `[0-9+\-*/()]` |
| `news.py` | 2 | RSS VnExpress, Tuổi Trẻ, Thanh Niên, VietnamNet |
| `finance.py` | 4 | Tỷ giá, vàng SJC, cổ phiếu VN, VN-Index |
| `wiki.py` | 1 | Wikipedia VN search |
| `translate.py` | 1 | MyMemory free API VN↔EN |
| `reminder.py` | 3 | Parse VN natural time, lưu JSON |
| `expense.py` | 3 | SQLite `data/expenses.db`, tổng tháng, báo cáo |
| `kb_search.py` | 2 | Grep trong `data/knowledge_base/*.md` |
| `memory_kg.py` | 4 | Knowledge graph JSON — entity + observations |
| `file_ops.py` | 4 | CRUD sandboxed `data/files/` |
| `url_fetch.py` | 1 | HTML → clean text |
| `database.py` | 2 | SQL read-only (SQLite default, Postgres optional) |

### Env-gated (11 modules, 46 tools)

| Module | N | Env vars | Deps |
|---|---|---|---|
| `home_assistant.py` | 5 | `HA_URL`, `HA_TOKEN` | stdlib |
| `calendar_gcal.py` | 3 | `GOOGLE_ACCESS_TOKEN` | stdlib |
| `web_search.py` | 1 | `BRAVE_API_KEY` | stdlib |
| `apify_scraper.py` | 2 | `APIFY_TOKEN` | stdlib |
| `notion_workspace.py` | 1 | `NOTION_TOKEN` | stdlib |
| `github_repo.py` | 3 | `GITHUB_TOKEN`, `GITHUB_REPO` | stdlib |
| `slack_chat.py` | 2 | `SLACK_BOT_TOKEN` | stdlib |
| `telegram_bot.py` | 2 | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | stdlib |
| `pc_control.py` | 18 | `ENABLE_PC_CONTROL=1` | `pyautogui`, `pyperclip` |
| `browser_playwright.py` | 6 | `ENABLE_BROWSER_PLAYWRIGHT=1` | `playwright` + chromium |
| `scheduler.py` | 3 | `ENABLE_SCHEDULER=1` + Telegram | `apscheduler` |

### Shared

- `tools/_common.py` — `_reply()` prefix helper + `_read_company_section()` parser
- `tools/__init__.py` — package marker

## data/ — runtime (gitignored)

```
data/
├── knowledge_base/    # .md files searched bởi kb_search
├── files/             # sandbox của file_ops
├── notes.txt          # notes.py store
├── reminders.json     # reminder.py store
├── memory.json        # memory_kg store
├── expenses.db        # SQLite expense
├── user.db            # SQLite database.py default
├── pc_mode.json       # legacy (không dùng nữa)
└── screenshots/       # pc_control screenshot output
```

## docs/ — source of truth

```
docs/
├── project-overview-pdr.md       # mục tiêu + requirements
├── codebase-summary.md           # (file này)
├── code-standards.md             # pattern viết tool
├── system-architecture.md        # sequence diagram + data flow
├── project-roadmap.md            # phase progress
├── voice-commands-examples.md    # trigger phrases per tool
└── xiaozhi-agent-system-prompt.md # prompt paste vào xiaozhi.me
```

## plans/ — implementation history

- `plans/reports/` — research + scout output
- `plans/{date}-{slug}/` — per-feature plan dirs với phase files

## Config files

| File | Purpose |
|---|---|
| `.env` | Local secrets, gitignored |
| `.env.example` | Template với mọi env var |
| `.gitignore` | Exclude `.env`, `data/`, `__pycache__`, `.venv/` |
| `requirements.txt` | Core deps + optional comments |
| `company_data.md` | Company info sections đọc bởi `company.py` |

## Key patterns

1. **`_reply()` prefix** — mọi tool response prepend ack text tránh speculative TTS hallucination
2. **Verbose docstring** với `GỌI TOOL NÀY KHI...` trigger phrases
3. **Env gate pattern** trong `server.py`: `if os.getenv("X"): module.register(mcp)`
4. **Stdlib-first** — urllib, json, sqlite3, subprocess; optional deps chỉ khi bật env gate
5. **Safe failure** — tool errors return graceful VN message, không throw
