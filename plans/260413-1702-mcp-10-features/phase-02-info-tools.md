---
phase: 2
title: Info tools — News VN, Currency/Gold, Wikipedia, Translate
status: pending
effort: 2h
priority: high
---

# Phase 2: Info tools (no-auth, high ROI)

## Context
4 features đều không cần API key, value rất cao cho daily use. Làm chung 1 phase vì pattern giống nhau (HTTP GET → parse → `_reply`).

## Features

### 2.1 News VN (RSS aggregator)
**Tools:** `lay_tin_moi_nhat()`, `doc_bao(nguon)`

**Sources (free RSS):**
- VnExpress: `https://vnexpress.net/rss/tin-moi-nhat.rss`
- Tuổi Trẻ: `https://tuoitre.vn/rss/tin-moi-nhat.rss`
- Thanh Niên: `https://thanhnien.vn/rss/home.rss`
- VietnamNet: `https://vietnamnet.vn/rss/home.rss`

**Dep:** `feedparser` (`pip install feedparser`)

**Return format:**
```
Đã lấy tin thành công.

1. [VnExpress] <title>
2. [Tuổi Trẻ] <title>
3. [Thanh Niên] <title>
...
```

Max 5 headlines per call.

### 2.2 Currency + Gold
**Tools:** `lay_ty_gia(tien_te)`, `gia_vang_sjc()`

**Sources:**
- Currency: `https://api.exchangerate.host/latest?base=USD&symbols=VND,EUR,JPY,KRW,CNY` (free, no key)
- Gold SJC: scrape `https://sjc.com.vn/` hoặc `https://cafef.vn/du-lieu/gia-vang-hom-nay.chn`

**Dep:** None (urllib + regex)

**Return format:**
```
Đã lấy tỷ giá thành công.

1 USD = 25,XXX VND
1 EUR = 27,XXX VND
1 JPY = 170 VND
```

### 2.3 Wikipedia search
**Tool:** `tim_wiki(tu_khoa)`

**API:** `https://vi.wikipedia.org/api/rest_v1/page/summary/{title}` (Vietnamese wiki)

**Dep:** None

**Return format:**
```
Đã tìm thấy kết quả.

<summary first 300 chars>
```

### 2.4 Translate VN ↔ EN
**Tool:** `dich(text, tu="vi", sang="en")`

**Option A:** `googletrans==4.0.0rc1` (unofficial, might break)
**Option B:** LibreTranslate self-host (stable nhưng cần setup)
**Option C (recommended):** Call MyMemory free API `https://api.mymemory.translated.net/get?q={text}&langpair={src}|{tgt}` — no key, 5000 chars/day free

**Dep:** None (MyMemory via urllib)

## Files to create

- `tools/news.py`
- `tools/finance.py` (currency + gold here; stocks phase 4)
- `tools/wiki.py`
- `tools/translate.py`

## Files to modify

- `server.py` → add `news.register(mcp)`, `finance.register(mcp)`, `wiki.register(mcp)`, `translate.register(mcp)`
- `requirements.txt` (create) → `feedparser`

## Implementation steps

1. `pip install feedparser`
2. Create `tools/news.py` — parse 4 RSS feeds, return top 5 mixed
3. Create `tools/finance.py` — 2 tools: currency (exchangerate.host) + gold (SJC scrape)
4. Create `tools/wiki.py` — Wikipedia REST summary API
5. Create `tools/translate.py` — MyMemory API call
6. Register in `server.py`
7. Test each via voice

## Todo

- [ ] `pip install feedparser`
- [ ] `tools/news.py` — RSS aggregator, 5 headlines max
- [ ] `tools/finance.py` — currency + gold
- [ ] `tools/wiki.py` — Wikipedia summary
- [ ] `tools/translate.py` — MyMemory translation
- [ ] Register 4 modules in `server.py`
- [ ] Create `requirements.txt`
- [ ] Voice test: "tin mới", "tỷ giá đô", "giá vàng", "Hồ Chí Minh là ai", "dịch chào buổi sáng"

## Error handling pattern

```python
try:
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))
    # ... parse
    return _reply(formatted)
except Exception as e:
    return f"Không thể lấy dữ liệu: {str(e)[:100]}"
```

## Success criteria

- 4 new tools callable via voice
- Response < 3 seconds for each
- Graceful fallback on network errors
- Vietnamese output, phù hợp TTS

## Risks

- RSS feed format thay đổi → feedparser robust, OK
- SJC scrape fragile → add 2 fallback sources
- MyMemory rate limit 5000 chars/day → đủ cho voice use case
- Wikipedia titles không khớp exact → thử search API trước summary API
