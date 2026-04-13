---
phase: 4
title: VN Stocks — giá cổ phiếu + VN-Index
status: pending
effort: 1h
priority: medium
---

# Phase 4: VN Stocks

## Context
Scraping chứng khoán VN từ nguồn public. Đơn giản vì chỉ 1 file module.

## Features

### 4.1 Stock price
**Tool:** `gia_co_phieu(ma_ck: str)` — "VCB", "FPT", "VIC"...

### 4.2 VN-Index
**Tool:** `vnindex_hien_tai()` — giá + % thay đổi

## Sources (chọn 1, fallback sang source khác)

**Primary:** VNDirect public API
```
https://api-finfo.vndirect.com.vn/v4/stock_prices?q=code:VCB&sort=date:desc&size=1
```
Response JSON, không cần key.

**Fallback:** Scrape CafeF
```
https://s.cafef.vn/Lich-su-giao-dich-VCB-1.chn
```
Parse HTML với regex.

**For VN-Index:**
```
https://api-finfo.vndirect.com.vn/v4/indices?q=code:VNINDEX
```

## Files to create

- `tools/stocks.py` — hoặc merge vào `tools/finance.py` từ phase 2

## Implementation

```python
import json, urllib.request
from ._common import _reply

VNDIRECT_API = "https://api-finfo.vndirect.com.vn/v4/stock_prices?q=code:{}&sort=date:desc&size=1"

def register(mcp):
    @mcp.tool()
    def gia_co_phieu(ma_ck: str) -> str:
        """Trả về giá cổ phiếu VN (VCB, FPT, VIC, HPG...) — giá đóng cửa gần nhất.

        GỌI TOOL NÀY KHI người dùng hỏi về: giá cổ phiếu, chứng khoán, mã XYZ bao nhiêu.
        Ví dụ: "giá VCB", "chứng khoán FPT", "HPG hôm nay", "mã VIC bao nhiêu".
        """
        ma_ck = ma_ck.upper().strip()
        try:
            url = VNDIRECT_API.format(ma_ck)
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            items = data.get('data', [])
            if not items:
                return f"Không tìm thấy mã {ma_ck}."
            item = items[0]
            close = item.get('close')
            change_pct = item.get('percentChange', 0)
            date = item.get('date', '')
            return _reply(
                f"Cổ phiếu {ma_ck} ngày {date}: "
                f"giá đóng cửa {close:,} đồng, "
                f"{'tăng' if change_pct >= 0 else 'giảm'} {abs(change_pct):.2f}%."
            )
        except Exception as e:
            return f"Không lấy được giá {ma_ck}: {str(e)[:100]}"

    @mcp.tool()
    def vnindex_hien_tai() -> str:
        """Trả về chỉ số VN-Index hiện tại (điểm số và % thay đổi).

        GỌI TOOL NÀY KHI người dùng hỏi: VN-Index, chỉ số chứng khoán, thị trường hôm nay.
        """
        # Similar VNDirect API call for indices
        ...
```

## Todo

- [ ] Research VNDirect API response schema (test với curl)
- [ ] Create `tools/stocks.py`
- [ ] 2 tools: `gia_co_phieu`, `vnindex_hien_tai`
- [ ] Register in `server.py`
- [ ] Voice test: "giá VCB", "VN-Index hôm nay"

## Success criteria

- Query trả về trong < 2s
- Format số có dấu phẩy (25,500 đồng)
- Mã không tồn tại → error message rõ ràng

## Risks

- VNDirect có thể thêm CORS/auth → fallback scraping CafeF
- Voice STT có thể nghe nhầm mã (VCB → "V C B" hoặc "vi xi bê") → LLM tự normalize trước khi gọi tool
- Thời gian ngoài giờ giao dịch → trả close price gần nhất, vẫn valid
