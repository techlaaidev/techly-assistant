---
phase: 1
title: Modular refactor — split server.py into tools/ package
status: pending
effort: 1h
priority: critical
---

# Phase 1: Modular refactor

## Context
`server.py` hiện tại ~230 lines với 12 tools. Sắp thêm 18+ tools → phải tách modules ngay.

## Goal
Tách `server.py` thành package `tools/` với mỗi feature 1 file. Không thay đổi behavior, chỉ reorganize.

## Files to create

```
tools/__init__.py
tools/_common.py        # _reply, _ACK_PREFIX, BASE_DIR, _read_company_section
tools/company.py        # 6 existing company tools
tools/time_tool.py      # lay_thoi_gian_hien_tai
tools/weather.py        # lay_thoi_tiet + _VN_CITY_COORDS
tools/notes.py          # ghi_chu, doc_ghi_chu, xoa_ghi_chu
tools/calc.py           # tinh_toan
```

## Files to modify

- `server.py` → chỉ còn import + register + `mcp.run()`

## Implementation steps

1. Create `tools/__init__.py` (empty)
2. Create `tools/_common.py` with:
   - `BASE_DIR = Path(__file__).parent.parent`
   - `COMPANY_DATA_FILE`, `NOTES_FILE`
   - `_ACK_PREFIX`, `_reply()`
   - `_read_company_section()`
3. For each tool file: import `mcp` instance from `server` via lazy binding, OR use a register pattern
4. **Register pattern**: each tool file exposes `register(mcp)` function that takes the FastMCP instance and decorates tools
5. Rewrite `server.py`:
   ```python
   from mcp.server.fastmcp import FastMCP
   from tools import company, time_tool, weather, notes, calc

   mcp = FastMCP("Techla AI - Trợ lý")
   company.register(mcp)
   time_tool.register(mcp)
   weather.register(mcp)
   notes.register(mcp)
   calc.register(mcp)

   if __name__ == "__main__":
       mcp.run(transport="stdio")
   ```

## Example: tools/company.py pattern

```python
from ._common import _reply, _read_company_section

def register(mcp):
    @mcp.tool()
    def lay_doanh_thu() -> str:
        """..."""
        return _reply(_read_company_section("Doanh thu"))
    # ... 5 more tools
```

## Todo

- [ ] Create `tools/` directory + `__init__.py`
- [ ] Extract helpers → `tools/_common.py`
- [ ] Move 6 company tools → `tools/company.py`
- [ ] Move time tool → `tools/time_tool.py`
- [ ] Move weather + city coords → `tools/weather.py`
- [ ] Move 3 notes tools → `tools/notes.py`
- [ ] Move calculator → `tools/calc.py`
- [ ] Rewrite `server.py` as entry point with register() calls
- [ ] Test: restart `mcp_pipe.py`, verify all 12 tools still work

## Success criteria

- `mcp_pipe.py` spawns `server.py` without error
- `tools/list` request returns 12 tools (same as before)
- Test 1 tool per module via voice (e.g. "doanh thu", "mấy giờ", "thời tiết hà nội", "ghi chú test", "1+1")

## Risks

- FastMCP decorator pattern — `@mcp.tool()` expects `mcp` instance at decoration time. Using register(mcp) function sidesteps this.
- Import cycles — `tools/_common.py` should NOT import from `server.py`

## Next phase unlock
Phase 2 (info tools) có thể bắt đầu song song ngay sau khi Phase 1 xong.
