# Techly Assistant — Project Overview & PDR

## Problem

Xiaozhi ESP32-S3 firmware khoá — chỉ có thể custom qua **MCP endpoint** (WebSocket) ở xiaozhi.me dashboard. Cloud LLM của Xiaozhi (GPT-5) không hiểu ngữ cảnh tiếng Việt + dữ liệu riêng của user (doanh thu, KH VIP, PC local).

Cần lớp **MCP server tự host** cung cấp custom tools tiếng Việt để voice assistant trở nên hữu ích cho business (công ty) + personal (chi tiêu, nhắc nhở, PC automation).

## Goal

Build MCP server duy nhất thoả:

1. **Tiếng Việt natural** — user nói sao LLM gọi đúng tool đó
2. **85+ tools** cover: business data, finance, news, knowledge, memory, PC automation, browser control, scheduled notifications
3. **Stdlib-first** — ít dep ngoài, dễ deploy Windows
4. **Env-gated integrations** — GitHub/Slack/HA/GCal/Notion… chỉ load khi có token
5. **Privacy local** — data ở máy user (SQLite, JSON, markdown), không upload

## Non-goals

- **Không** flash firmware ESP32 (không có quyền)
- **Không** custom audio protocol (Xiaozhi cloud xử lý ASR/TTS)
- **Không** push TTS ngược xuống ESP32 (pull-only constraint)
- **Không** local LLM / wakeword (đã có trong Xiaozhi)

## Users & persona

**Primary:** Techla AI team (VN) + founder
- Trợ lý voice ở bàn làm việc Windows
- Cần hỏi nhanh số liệu công ty + điều khiển PC + nhắc nhở

**Secondary:** Dev khác copy project làm assistant riêng
- Clone repo, set `.env`, chạy `python mcp_pipe.py`

## Functional requirements

### F1. Always-on tools (39 tools, no auth)
Company data, time, weather, news, finance, wiki, translate, reminder (local), expense (SQLite), knowledge base search, memory graph, file ops, url fetch, calc, database query (read-only).

### F2. Env-gated integrations (46 tools)
Home Assistant, Google Calendar, Brave Search, Apify, Notion, GitHub, Slack, Telegram, PC Control (PyAutoGUI), Browser (Playwright), Scheduler (APScheduler + Telegram proactive).

### F3. Proactive channel
Vì Xiaozhi cloud pull-only, dùng **Telegram bot** làm channel đẩy thông báo chủ động (reminder, alert). Tool `dat_lich_nhac_chu_dong` schedule job qua APScheduler → fire → push qua Telegram Bot API.

### F4. Voice UX
- Tool response prepend `_reply()` prefix để tránh LLM hallucinate "không tìm thấy" trong lúc speculative TTS
- Docstring verbose với trigger phrases tiếng Việt
- Empty data → explicit "chưa có" message
- System prompt ở xiaozhi.me bắt LLM đợi tool, không filler

## Non-functional requirements

- **Latency:** local tool < 100ms, HTTP tool 200-500ms, heavy scrape 1-3s
- **Memory:** server idle < 100MB, scheduler jobs in-memory
- **Security:** `.env` gitignored, DB read-only, file ops sandboxed, calc safe-eval, HTTP timeouts 10s
- **Reliability:** errors return graceful VN text, không throw exception

## Success metrics

- **Trigger accuracy:** 90%+ voice command gọi đúng tool
- **Zero downtime deployment:** restart bridge < 2s
- **Tool coverage:** 85 tools hoạt động E2E qua ESP32 voice

## Constraints

- **Windows 10 host** (Python 3.14)
- **ESP32-S3 firmware đã fix** — không flash được
- **Xiaozhi cloud MCP client pull-only** — không push proactive TTS
- **Speculative TTS cloud** — mitigate bằng system prompt + `_reply()` pattern
- **No hardcoded secrets** — tất cả token qua `.env`
