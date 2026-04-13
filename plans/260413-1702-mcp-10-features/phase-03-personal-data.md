---
phase: 3
title: Personal data — Reminder with time + Expense tracker
status: pending
effort: 2h
priority: high
---

# Phase 3: Personal data tools

## Context
2 features cần local persistence + Vietnamese time parsing.

## Features

### 3.1 Reminder with time
**Tools:**
- `them_nhac(thoi_gian: str, noi_dung: str)` — "3h chiều mai họp" → parse + store
- `xem_nhac_sap_toi()` — list pending reminders
- `xoa_nhac(id: int)` — remove by index

**Storage:** `data/reminders.json` — list of `{id, time_iso, content, created_at}`

**Dep:** `dateparser` (`pip install dateparser`) — parse Vietnamese time expressions

**Example parse:**
- "3h chiều mai" → `2026-04-14T15:00:00`
- "9h sáng thứ 6" → next Friday 9AM
- "20 phút nữa" → `now + 20min`

**Return format:**
```
Đã lưu nhắc thành công.

Nhắc bạn vào 15h ngày 14/04/2026: họp với sếp
```

**Note:** Server KHÔNG có background task trigger — LLM chỉ list khi user hỏi. Không phải alarm thật.

### 3.2 Expense tracker
**Tools:**
- `ghi_chi_tieu(so_tien: int, danh_muc: str, ghi_chu: str = "")`
- `tong_chi_thang(thang: int = 0)` — tháng hiện tại nếu 0
- `bao_cao_chi_tieu()` — breakdown by category this month

**Storage:** `data/expenses.db` (SQLite) — table `expenses(id, amount, category, note, created_at)`

**Dep:** None (sqlite3 stdlib)

**Example:**
- "hôm nay tiêu 50k ăn trưa" → `ghi_chi_tieu(50000, "ăn uống", "ăn trưa")`
- "tháng này tiêu bao nhiêu" → `tong_chi_thang()`

**Return format:**
```
Đã ghi chi tiêu thành công.

Bạn đã ghi: 50.000đ cho danh mục "ăn uống"
Tổng chi tháng này: 2.350.000đ
```

## Files to create

- `tools/reminder.py`
- `tools/expense.py`
- `data/` directory
- `data/reminders.json` (empty `[]` on first run)
- `data/expenses.db` (auto-create on first run)

## Implementation steps

1. `pip install dateparser`
2. Create `tools/reminder.py`:
   - Load/save `reminders.json` with UTF-8
   - Parse time with `dateparser.parse(text, languages=['vi', 'en'], settings={'PREFER_DATES_FROM': 'future'})`
   - ID = max(ids) + 1
3. Create `tools/expense.py`:
   - Init SQLite table if not exists
   - Insert, query by month, group by category
4. Register in `server.py`
5. Voice test

## Todo

- [ ] `pip install dateparser`
- [ ] `tools/reminder.py` — 3 tools: add/list/delete
- [ ] `tools/expense.py` — 3 tools: log/total/breakdown
- [ ] Create `data/` directory auto (pathlib mkdir parents=True, exist_ok=True)
- [ ] Register in `server.py`
- [ ] Voice test reminders: "nhắc tôi 5 phút nữa uống nước", "có nhắc gì không"
- [ ] Voice test expense: "tiêu 100k cà phê", "tháng này tiêu bao nhiêu"

## Success criteria

- Reminders persist across server restart
- Vietnamese time parsing accurate for common phrases
- Expense breakdown returns sorted by amount desc
- Numbers format Vietnamese (50.000đ not 50000)

## Risks

- `dateparser` tiếng Việt chưa hoàn hảo → test kỹ, fallback manual regex
- SQLite file lock nếu multiple instances → chỉ 1 `mcp_pipe.py` chạy, OK
- User có thể nói "k" hoặc "nghìn" thay vì số → parse "50k" → 50000

## Helper: Vietnamese number parsing

```python
def parse_vn_amount(text: str) -> int:
    text = text.lower().replace(" ", "").replace(".", "").replace(",", "")
    if "k" in text or "nghìn" in text or "nghin" in text:
        num = int(re.search(r'(\d+)', text).group(1))
        return num * 1000
    if "tr" in text or "triệu" in text or "trieu" in text:
        num = int(re.search(r'(\d+)', text).group(1))
        return num * 1_000_000
    return int(re.search(r'(\d+)', text).group(1))
```
