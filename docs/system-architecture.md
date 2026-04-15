# System Architecture — Techly Assistant

## 2-layer model

Xiaozhi ESP32 ↔ cloud là layer **black-box** (firmware cố định, custom audio protocol). Cloud ↔ MCP server là layer **vanilla MCP** qua WebSocket — đây là nơi ta control được.

```
┌─────────────┐     custom audio     ┌──────────────────┐     JSON-RPC MCP      ┌─────────────────┐
│   ESP32-S3  │  ←───────────────→   │  Xiaozhi cloud   │  ←──────────────────→ │  mcp_pipe.py    │
│  mic + loa  │     (ASR/LLM/TTS)    │   xiaozhi.me     │      wss://           │  (bridge)       │
└─────────────┘                      └──────────────────┘                       └────────┬────────┘
                                                                                          │ stdio
                                                                                          ▼
                                                                                 ┌─────────────────┐
                                                                                 │   server.py     │
                                                                                 │  (FastMCP)      │
                                                                                 └────────┬────────┘
                                                                                          │
                                                                                          ▼
                                                                                 ┌─────────────────┐
                                                                                 │  tools/*.py     │
                                                                                 │  27 modules     │
                                                                                 └─────────────────┘
```

**Hệ quả:**
- Ta không push được âm thanh/TTS ngược xuống ESP32 ngoài phản hồi cho tool call (cloud là MCP **client**, không listen push)
- Proactive notification → đi kênh khác (Telegram)

## Request flow (voice → tool → voice)

```
1. User nói "Doanh thu tháng 3"
2. ESP32 mic → Xiaozhi cloud ASR → text
3. Cloud LLM (GPT-5) đọc tools list, match "doanh thu" → tool `lay_doanh_thu`
4. Cloud gửi JSON-RPC tools/call qua WSS → mcp_pipe.py
5. Bridge forward qua stdin của server.py subprocess
6. FastMCP dispatch → tools/company.py::lay_doanh_thu
7. Tool đọc company_data.md section "Doanh thu"
8. Return _reply("Đã lấy thông tin... [data]")
9. Server stdout → bridge patch_response → WSS → cloud
10. Cloud LLM compose reply → TTS → ESP32 loa
```

## Proactive flow (scheduled → Telegram)

```
1. User nói "Nhắc tôi uống nước sau 30 phút"
2. [voice → tool → voice] chain gọi dat_lich_nhac_chu_dong(noi_dung="uống nước", sau_phut=30)
3. Tool schedule APScheduler job:
   - trigger: DateTrigger(run_date=now+30min)
   - callback: _push_telegram("uống nước")
4. Return _reply("Đã đặt lịch nhắc lúc HH:MM...")
5. [30 phút sau] scheduler thread fire _push_telegram
6. urllib.request POST https://api.telegram.org/bot{TOKEN}/sendMessage
7. User nhận push notification qua Telegram mobile app
```

**Tại sao không push TTS ngược ESP32?**
- Xiaozhi cloud không accept notification từ MCP server (client MCP chỉ nhận response cho request đã gửi)
- `mcp_pipe.stderr_logger()` chỉ log stderr ra console, không forward lên WSS
- Experimental hack forward JSON stderr lên WSS đã thử và fail → đã xoá

## Bridge internals (mcp_pipe.py)

3 async tasks chạy song song:

| Task | Direction | Purpose |
|---|---|---|
| `stderr_logger` | server.stderr → console | Log Python exceptions, debug info |
| `xiaozhi_to_mcp_server` | WSS → server.stdin | Forward tool calls; intercept `ping` method tại bridge, respond `{keepalive: true, alive: "ok"}` non-empty để LLM không misinterpret |
| `mcp_server_to_xiaozhi` | server.stdout → WSS | Forward tool responses qua `patch_response()` — simplify `messages` / `conversations` structured content |

**Ping intercept** tại bridge level giúp:
- Không spam server với health checks
- Response non-empty tránh LLM gọi "không có dữ liệu" nhầm

## FastMCP bootstrapping (server.py)

```python
1. Load .env file (manual parser, không cần python-dotenv)
2. Import all tools/*.py
3. Instantiate FastMCP("Techla AI - Trợ lý")
4. Always-register 16 modules (core tools)
5. Conditional register 11 modules theo env gate:
   if os.getenv("HA_URL") and os.getenv("HA_TOKEN"):
       home_assistant.register(mcp)
   if os.getenv("ENABLE_PC_CONTROL", "").lower() in ("1", "true", "yes"):
       pc_control.register(mcp)
   ...
6. mcp.run(transport="stdio")
```

## Data stores

| Store | Module | Path | Format |
|---|---|---|---|
| Notes | `notes.py` | `data/notes.txt` | Plain text lines |
| Reminders | `reminder.py` | `data/reminders.json` | JSON list |
| Expenses | `expense.py` | `data/expenses.db` | SQLite |
| Memory KG | `memory_kg.py` | `data/memory.json` | JSON dict |
| Knowledge base | `kb_search.py` | `data/knowledge_base/*.md` | Markdown |
| File ops sandbox | `file_ops.py` | `data/files/*` | Any |
| Main DB | `database.py` | `data/user.db` | SQLite (read-only) |
| Scheduled jobs | `scheduler.py` | **in-memory** | APScheduler default jobstore |

**Note:** Scheduler jobstore in-memory → lịch nhắc mất khi restart server. Upgrade path: `SQLAlchemyJobStore` để persist vào `data/scheduler.db`.

## Security boundaries

| Layer | Protection |
|---|---|
| Secrets | `.env` gitignored, no hardcoded tokens |
| SQL | Regex whitelist `SELECT`, block DML/DDL |
| File ops | `Path.resolve()` check không thoát `data/files/` |
| Calc | AST-free eval với whitelist `[0-9+\-*/()]`, `__builtins__: {}` |
| HTTP | Timeout 10s + try/except wrap mọi urllib call |
| PC control | Opt-in via `ENABLE_PC_CONTROL`, PyAutoGUI fail-safe (0,0) |
| Browser | Opt-in via `ENABLE_BROWSER_PLAYWRIGHT` |

## Extension points

Để thêm tool mới:

1. Tạo `tools/your_feature.py` với signature `def register(mcp): ...`
2. Mỗi function wrap `@mcp.tool()` với verbose docstring + `GỌI TOOL NÀY KHI` trigger
3. Return `_reply("...")` text response
4. Import + register trong `server.py` (conditional nếu cần env var)
5. Restart `mcp_pipe.py` — cloud tự discover qua `tools/list` request
