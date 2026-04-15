# Project Roadmap — Techly Assistant

## Status snapshot

- **Version:** active dev
- **Updated:** 2026-04-15
- **Tools live:** 85 / 27 modules
- **Infra:** ESP32-S3 ↔ xiaozhi.me cloud ↔ `mcp_pipe.py` ↔ `server.py` ↔ tools/

## ✅ Completed phases

### Phase 0 — Bootstrap (done)
- FastMCP stdio server + WSS bridge
- 28 Vietnamese tools initial
- System prompt ở xiaozhi.me dashboard
- `_reply()` pattern fix speculative TTS

### Phase 1 — Core expansion (done)
- +10 integrations: Brave, Apify, Notion, GitHub, Slack, Telegram, memory_kg, file_ops, url_fetch, database
- Env-gated pattern
- KB search + knowledge graph

### Phase 2 — PC automation (done)
- `pc_control.py` (18 tools) — PyAutoGUI mouse/keyboard/screenshot/app launch
- Fail-safe corner (0,0)
- Clipboard Vietnamese via pyperclip

### Phase 3 — Browser automation (done)
- `browser_playwright.py` (6 tools) — semantic click bằng text, fill form, scrape
- Async Playwright API
- Multi-tier click strategy với JS fallback

### Phase 4 — Proactive channel (done, 2026-04-15)
- APScheduler skeleton `tools/scheduler.py` (3 tools)
- `dat_lich_nhac_chu_dong` → Telegram push qua Bot API
- In-memory jobstore (upgrade path: SQLAlchemy)
- Confirmed proactive TTS xuống ESP32 **không khả thi** (pull-only MCP), stderr hack đã xoá

### Phase 5 — Cleanup (done, 2026-04-15)
- Xoá tool thừa: `browser_use_agent.py`, `goose_agent.py`, `click_thong_minh`
- Xoá file orphan: `find_python.ps1`, `mcp-status-dashboard.py`, `ESP32-XIAOZHI-INTEGRATION.md`
- `.env` / `.env.example` / `requirements.txt` sync
- Docs refresh: README + voice-commands-examples

## 🚧 In progress

### Jarvis Phase 1 — Personality + Vision + Music
Plan: `plans/260415-1400-jarvis-phase-1-personality-vision-music/`

| Sub-phase | Effort | Status | Blocker |
|---|---|---|---|
| Personality layer (system prompt + Jarvis voice) | ~1h | Queued | Test Xiaozhi char limit |
| Screen Vision (OpenAI gpt-4o-mini + screenshot tool) | ~2-3h | Queued | OpenAI credit top-up |
| Spotify Control (oauth + playback API) | ~3h | Queued | Spotify Premium + Developer App |

## 🗺️ Backlog

### Persistence upgrade
- **Scheduler SQLAlchemyJobStore** → persist jobs qua restart
- Path: `data/scheduler.db`
- Dep thêm: `sqlalchemy`

### Reliability
- Auto-reconnect WSS khi Xiaozhi cloud disconnect
- Retry với exponential backoff
- Health endpoint để systemd/nssm monitor

### Integrations khả thi
- **Zalo Official Account API** — gửi tin Zalo thay Telegram (VN-native)
- **Grammarly / Ngrok webhook** cho push dev workflow
- **VNPay sandbox** đọc giao dịch (expense auto-import)

### Developer experience
- CLI debug tool để test tool call local (không cần ESP32)
- Dashboard web simple show tool registry + env status
- Unit test framework cho tool response format

### Known limitations cần giải quyết
- **Google Calendar token 1h** — implement refresh token flow
- **Speculative TTS** — vẫn còn edge case khi LLM gọi wrong tool trước khi speak
- **Xiaozhi char limit 2000** cho system prompt — cần prune khi thêm tool

## ❌ Anti-roadmap (không làm)

- **Flash ESP32 firmware** — không có quyền hardware
- **Local LLM / whisper** — đã có ở Xiaozhi
- **Custom wakeword** — đã có "Xiaozhi" default
- **Raw audio protocol** — firmware đã fix
- **Speaker recognition** — cloud block raw PCM
- **Proactive TTS push ESP32** — confirmed impossible, dùng Telegram

## Success metrics (Q2 2026)

- [ ] 90%+ trigger accuracy across 85 tools
- [ ] < 2s tool-to-voice latency cho local tools
- [x] Proactive channel work qua Telegram (done Phase 4)
- [ ] 1 Jarvis feature live (personality hoặc vision)
- [ ] Scheduler persistent qua restart
