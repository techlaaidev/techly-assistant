---
title: MCP server — 10 features cho Techla AI voice assistant
status: pending
created: 2026-04-13
mode: fast
project: xiaozhi-project
---

# Plan: MCP Server 10 Features

Mở rộng `server.py` từ 12 tools cơ bản → 22+ tools với 10 features mới cho voice assistant Techla AI (chạy qua Xiaozhi cloud + ESP32).

## Mục tiêu
- Refactor `server.py` thành package modular (mỗi feature 1 file)
- Thêm 10 features đã chốt (xem brainstorm prior)
- Mọi tool đều: tiếng Việt, có ack prefix, có docstring trigger phrases
- Không break tools cũ

## Phase overview

| # | Phase | Effort | Tools added | Deps | Status |
|---|---|---|---|---|---|
| 1 | [Modular refactor](phase-01-modular-refactor.md) | 1h | 0 (refactor) | — | pending |
| 2 | [Info tools](phase-02-info-tools.md) | 2h | News, Currency/Gold, Wikipedia, Translate | feedparser, googletrans | pending |
| 3 | [Personal data](phase-03-personal-data.md) | 2h | Reminder, Expense tracker | dateparser, sqlite | pending |
| 4 | [VN stocks](phase-04-vn-stocks.md) | 1h | Stock price, VN-Index | requests | pending |
| 5 | [Knowledge base RAG](phase-05-knowledge-base-rag.md) | 2h | Local docs search | — (grep) | pending |
| 6 | [Home Assistant IoT](phase-06-iot-home-assistant.md) | 2h | Light, AC, status | HA REST API token | pending |
| 7 | [Google Calendar](phase-07-google-calendar.md) | 3h | Today events, add event | google-auth, calendar API | pending |

**Tổng:** ~13 hours work, 7 phases, 18+ new tools.

## Key insights

- **Modular first** — tránh `server.py` thành monolith 1000+ lines
- **No-auth features first** — News/Currency/Wikipedia → instant value, không setup phức tạp
- **Auth-required last** — HA + Google Calendar có barrier setup, làm khi user sẵn sàng
- **All tools cùng pattern**: `_reply()` prefix + verbose docstring với trigger phrases (xem `server.py` hiện tại làm reference)
- **Reuse existing helpers**: `_reply()`, `_read_company_section()`, BASE_DIR

## Architecture sau refactor

```
xiaozhi-project/
├── server.py                # Entry point: import & register tools
├── tools/
│   ├── __init__.py
│   ├── _common.py           # _reply, _ACK_PREFIX, BASE_DIR
│   ├── company.py           # 6 company tools (existing)
│   ├── time_tool.py         # lay_thoi_gian_hien_tai
│   ├── weather.py           # lay_thoi_tiet
│   ├── notes.py             # ghi_chu, doc_ghi_chu, xoa_ghi_chu
│   ├── calc.py              # tinh_toan
│   ├── news.py              # NEW phase 2
│   ├── finance.py           # NEW phase 2 (currency/gold) + phase 4 (stocks)
│   ├── wiki.py              # NEW phase 2
│   ├── translate.py         # NEW phase 2
│   ├── reminder.py          # NEW phase 3
│   ├── expense.py           # NEW phase 3
│   ├── kb_search.py         # NEW phase 5
│   ├── home_assistant.py    # NEW phase 6
│   └── calendar_gcal.py     # NEW phase 7
├── data/
│   ├── reminders.json       # phase 3
│   ├── expenses.db          # phase 3 (sqlite)
│   └── knowledge_base/      # phase 5 (.md files)
└── company_data.md
```

## Constraints / non-goals

- **Không** tách thành microservices — tất cả vẫn 1 stdio MCP process
- **Không** dùng async tools — FastMCP sync đã đủ nhanh, đỡ phức tạp
- **Không** viết tests đơn vị riêng — voice testing là main QA
- **Không** integrate với xiaozhi-esp32-server local — chỉ dùng cloud + MCP bridge
- **Không** add UI quản lý — config qua file/env vars

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Cloud LLM speculative TTS issue chưa fix | High UX | Verbose tool descs + system prompt (đã làm) |
| Google Calendar OAuth phức tạp | Low | Phase 7 optional, có thể skip |
| HA cần local instance running | Low | Phase 6 chỉ làm khi user setup HA |
| Stock scraping bị block | Med | Fallback nhiều sources (CafeF, VNDirect) |
| Translate API rate limit | Med | Cache common phrases, fallback dictionary |

## Next steps after plan

1. Implement Phase 1 (refactor) — foundational, must complete trước phase khác
2. Implement Phase 2 → 3 → 4 → 5 (theo ROI thứ tự)
3. Phase 6, 7 chỉ làm khi user sẵn sàng setup HA / Google
4. Sau mỗi phase: restart `mcp_pipe.py`, test 1-2 voice commands
