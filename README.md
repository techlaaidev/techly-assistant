# Techly Assistant

MCP server cung cấp **85 custom tools** tiếng Việt cho voice assistant Xiaozhi (ESP32-S3 + cloud).

Bridge giữa Xiaozhi cloud (WebSocket) ↔ stdio MCP server với tools cho business + personal use + PC automation.

## Architecture

```
ESP32 (mic/loa) ↔ Xiaozhi cloud (ASR/LLM/TTS) ↔ MCP endpoint WebSocket
                                                        ↓
                                              mcp_pipe.py (bridge)
                                                        ↓
                                              server.py (FastMCP stdio)
                                                        ↓
                                              tools/ (27 modules, 85 tools)
```

**Proactive channel:** Xiaozhi cloud là MCP client pull-only — server **không** push TTS ngược về ESP32. Thông báo chủ động (reminder, alert) đi qua **Telegram bot** (`tools/scheduler.py` + `tools/telegram_bot.py`).

## Tools overview

**85 tools / 27 modules.** 39 always-on, 46 env-gated. Stdlib-first, optional deps chỉ khi bật feature tương ứng.

### ✅ Always-on (16 modules, no auth)

| Module | Tools | Description |
|---|---|---|
| `company.py` | 6 | Doanh thu, đơn hàng, thông tin công ty, KH VIP, sản phẩm, lịch họp |
| `time_tool.py` | 1 | Giờ hiện tại bằng tiếng Việt |
| `weather.py` | 1 | Thời tiết VN (open-meteo, no key) |
| `notes.py` | 3 | Ghi chú / đọc / xóa |
| `calc.py` | 1 | Tính toán an toàn (whitelist regex) |
| `news.py` | 2 | RSS VnExpress / Tuổi Trẻ / Thanh Niên / VietnamNet |
| `finance.py` | 4 | Tỷ giá, giá vàng SJC, cổ phiếu VN, VN-Index |
| `wiki.py` | 1 | Wikipedia tiếng Việt |
| `translate.py` | 1 | VN ↔ EN (MyMemory free API) |
| `reminder.py` | 3 | Nhắc có thời gian (parse VN tự nhiên) |
| `expense.py` | 3 | Ghi chi tiêu, tổng tháng, báo cáo (SQLite) |
| `kb_search.py` | 2 | Tìm trong tài liệu nội bộ (grep) |
| `memory_kg.py` | 4 | Knowledge graph lưu thực thể + observation |
| `file_ops.py` | 4 | Đọc/viết/xóa file sandboxed trong `data/files/` |
| `url_fetch.py` | 1 | Fetch URL → text sạch (no external dep) |
| `database.py` | 2 | Query DB read-only (SQLite default, Postgres optional) |

### ⚪ Conditional (env-gated)

| Module | Tools | Env vars | Use case |
|---|---|---|---|
| `home_assistant.py` | 5 | `HA_URL`, `HA_TOKEN` | Điều khiển đèn / điều hoà / công tắc |
| `calendar_gcal.py` | 3 | `GOOGLE_ACCESS_TOKEN` | Google Calendar view + add event |
| `web_search.py` | 1 | `BRAVE_API_KEY` | Tìm kiếm web qua Brave Search |
| `apify_scraper.py` | 2 | `APIFY_TOKEN` | Scrape 4000+ sites (Shopee, FB, Maps...) |
| `notion_workspace.py` | 1 | `NOTION_TOKEN` | Tìm pages/databases trong Notion |
| `github_repo.py` | 3 | `GITHUB_TOKEN`, `GITHUB_REPO` | PRs / Issues / Commits |
| `slack_chat.py` | 2 | `SLACK_BOT_TOKEN` | Post / đọc Slack messages |
| `telegram_bot.py` | 2 | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Gửi / đọc Telegram |
| `pc_control.py` | 18 | `ENABLE_PC_CONTROL=1` | Mở app, click, gõ phím, chụp màn hình (PyAutoGUI) |
| `browser_playwright.py` | 6 | `ENABLE_BROWSER_PLAYWRIGHT=1` | Điều khiển Chromium (click semantic, fill form, scrape) |
| `scheduler.py` | 3 | `ENABLE_SCHEDULER=1` + Telegram | Lịch nhắc chủ động — đẩy thông báo qua Telegram |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Core: `mcp`, `websockets`, `dateparser`.

Optional (chỉ cài khi bật feature tương ứng):
- `apscheduler` — khi `ENABLE_SCHEDULER=1`
- `pyautogui`, `pyperclip` — khi `ENABLE_PC_CONTROL=1`
- `playwright` + `python -m playwright install chromium` — khi `ENABLE_BROWSER_PLAYWRIGHT=1`

### 2. Configure `.env`

```bash
cp .env.example .env
```

**Required:** `XIAOZHI_MCP_WSS` (lấy từ xiaozhi.me agent settings).

**Optional:** tất cả integration khác — chỉ fill env var của feature bạn muốn dùng.

### 3. Run

```bash
python mcp_pipe.py
```

Bridge spawns `server.py` as stdio subprocess và connect tới Xiaozhi cloud WebSocket.

Output mong đợi:
```
✅ MCP server spawned PID: 1234
✅ Đã kết nối Xiaozhi
💓 ping id=1 → pong (non-empty, handled by bridge)
📨 Xiaozhi → MCP: {"method":"tools/list",...}
📤 MCP → Xiaozhi: {...42 tools...}
```

## Voice commands examples

### Company (always on)
- "Doanh thu tháng 3"
- "Hôm nay có bao nhiêu đơn"
- "Sản phẩm bán chạy nhất"
- "Lịch họp tuần này"

### Time / Weather / News
- "Mấy giờ rồi"
- "Thời tiết Sài Gòn"
- "Tin mới nhất"
- "Đọc báo Tuổi Trẻ"

### Finance
- "Tỷ giá đô"
- "Giá vàng SJC"
- "Giá cổ phiếu VCB"
- "VN-Index hôm nay"

### Personal
- "Tiêu 50 nghìn cà phê"
- "Tháng này tiêu bao nhiêu"
- "Nhắc tôi 3h chiều họp"
- "Dịch 'chào buổi sáng' sang tiếng Anh"

### Knowledge
- "Chính sách nghỉ phép" (local KB)
- "Hồ Chí Minh là ai" (Wikipedia)
- "Nhớ là tôi thích cà phê đen" (memory)
- "Đọc trang web https://..."

### If configured
- "Tìm trên web về Vingroup" (Brave)
- "Scrape top 10 quán phở Hà Nội" (Apify)
- "PR nào đang chờ review" (GitHub)
- "Gửi Slack 'meeting 3h'" (Slack)
- "Bật đèn phòng khách" (Home Assistant)
- "Lịch hôm nay" (Google Calendar)
- "Mở Chrome", "chụp màn hình" (PC Control)
- "Vào vnexpress.net rồi click tin mới nhất" (Browser Playwright)
- "Nhắc tôi sau 30 phút uống nước" → đẩy qua Telegram (Scheduler)

## Project structure

```
.
├── server.py                  # MCP entry point, registers all tools
├── mcp_pipe.py                # WebSocket bridge xiaozhi.me ↔ stdio
├── tools/                     # 1 file per feature
│   ├── _common.py             # shared _reply, _read_company_section, etc.
│   │
│   ├── company.py             # always-on
│   ├── time_tool.py
│   ├── weather.py
│   ├── notes.py
│   ├── calc.py
│   ├── news.py
│   ├── finance.py
│   ├── wiki.py
│   ├── translate.py
│   ├── reminder.py
│   ├── expense.py
│   ├── kb_search.py
│   ├── memory_kg.py
│   ├── file_ops.py
│   ├── url_fetch.py
│   ├── database.py
│   │
│   ├── home_assistant.py      # env-gated
│   ├── calendar_gcal.py
│   ├── web_search.py
│   ├── apify_scraper.py
│   ├── notion_workspace.py
│   ├── github_repo.py
│   ├── slack_chat.py
│   ├── telegram_bot.py
│   ├── pc_control.py          # PyAutoGUI automation (ENABLE_PC_CONTROL)
│   ├── browser_playwright.py  # Chromium control (ENABLE_BROWSER_PLAYWRIGHT)
│   └── scheduler.py           # proactive Telegram notifications (ENABLE_SCHEDULER)
│
├── data/
│   ├── knowledge_base/        # markdown files for kb_search
│   ├── files/                 # sandboxed file_ops area (auto)
│   ├── memory.json            # memory_kg store (auto, gitignored)
│   ├── expenses.db            # expense SQLite (auto, gitignored)
│   ├── reminders.json         # auto, gitignored
│   └── notes.txt              # auto, gitignored
│
├── company_data.md            # company info used by company.py
├── docs/
│   ├── xiaozhi-agent-system-prompt.md  # paste into xiaozhi.me dashboard
│   └── voice-commands-examples.md      # trigger phrases for every tool
├── plans/                     # implementation plans + research reports
├── requirements.txt
├── .env                       # local secrets, gitignored
├── .env.example               # template
└── .gitignore
```

## Tool design pattern

Mỗi tool follow pattern 4 bước:

1. **`_reply()` prefix** — prepend ack text "Đã lấy thông tin thành công..." để cloud LLM không hallucinate "không tìm thấy" trong lúc speculative TTS streaming
2. **Verbose docstring** với `GỌI TOOL NÀY KHI...` + ví dụ trigger phrases
3. **Empty data → explicit "chưa có" message** thay vì 0/null (LLM dễ interpret sai)
4. **Error → graceful Vietnamese message**, không throw exception

Example pattern:

```python
# tools/company.py
from ._common import _reply, _read_company_section

def register(mcp):
    @mcp.tool()
    def lay_doanh_thu() -> str:
        """Trả về doanh thu công ty theo từng tháng (số liệu triệu VND).

        GỌI TOOL NÀY KHI người dùng hỏi về: doanh thu, doanh số, lợi nhuận.
        Ví dụ: "doanh thu tháng 3", "công ty lời bao nhiêu".
        """
        return _reply(_read_company_section("Doanh thu"))
```

## Adding a new tool

1. Tạo `tools/your_feature.py` với `register(mcp)` function
2. Import + register trong `server.py`:
   ```python
   from tools import your_feature
   your_feature.register(mcp)  # hoặc conditional với env var
   ```
3. Restart `mcp_pipe.py`
4. Cloud LLM auto-discovery tool qua `tools/list` MCP request

## Security

- **`.env` gitignored** — chứa tokens (Xiaozhi JWT, Google access, HA, GitHub, Slack, Telegram, Apify, Brave, Notion, OpenAI)
- **No hardcoded secrets** — `mcp_pipe.py` + `server.py` đều đọc từ env
- **Database read-only** — whitelist regex chỉ cho `SELECT`, block `INSERT/UPDATE/DELETE/DROP/...`
- **File ops sandboxed** — chỉ trong `data/files/`, prevent directory traversal qua `Path.resolve()` check
- **Calculator safe eval** — whitelist `[0-9 +\-*/()]` only, `{"__builtins__": {}}` context
- **HTTP timeouts** — tất cả calls có `timeout=10` + `try/except` wrap
- **PC control opt-in** — `pc_control` chỉ load khi `ENABLE_PC_CONTROL=1`. Fail-safe: move chuột về (0,0) để abort action đang chạy
- **Browser opt-in** — `browser_playwright` chỉ load khi `ENABLE_BROWSER_PLAYWRIGHT=1`
- **Privacy block hook** — Claude Code tự động block read `.env` trừ khi user approve

## Performance

- **Tool response < 100ms** cho local tools (company, time, notes, calc, expense, KB)
- **~200-500ms** cho HTTP tools (weather, news, wiki, translate, Brave)
- **1-3s** cho heavy tools (Apify, scraping)
- **Ping intercept** — bridge tự handle ping, không forward đến server → clean logs + faster pong

## Known limitations

- **Pull-only MCP** — Xiaozhi cloud là MCP client, server không push được TTS xuống ESP32 ngoài phản hồi tool call. Workaround: proactive notification đi qua Telegram (`scheduler.py` + `telegram_bot.py`).
- **Scheduler jobstore in-memory** — lịch nhắc mất sau restart server. Upgrade path: `SQLAlchemyJobStore` để persist.
- **Google Calendar access token expires ~1h** — cần external refresh system
- **Speculative TTS** — xiaozhi cloud có thể speak filler trước khi tool trả về data. Fix bằng system prompt ở dashboard (file `docs/xiaozhi-agent-system-prompt.md`).
- **Function calling reliability** — GPT-5 đôi khi hallucinate tool call trong text thay vì native function call. Mitigation: verbose tool descriptions + system prompt strict.

## License

Internal use — Techla AI
