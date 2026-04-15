# Code Standards — Techly Assistant

## Language & style

- **Python 3.14**, stdlib-first
- **snake_case** function/variable (Python convention)
- **Docstring tiếng Việt** cho user-facing tools (cloud LLM đọc để match trigger)
- **Tên function = tên voice-friendly tiếng Việt** (ví dụ `lay_doanh_thu`, không phải `get_revenue`)
- **File size < 200 LOC** — nếu quá thì tách module. Exception: `pc_control.py` lớn vì nhóm 18 tools related.

## Tool module structure

Mỗi file trong `tools/` phải follow pattern:

```python
"""Module docstring — 1 câu mô tả scope."""
import os  # stdlib imports
import json

from ._common import _reply  # shared helper

# module-level constants nếu cần
_API_URL = "https://example.com/api"


def _helper() -> str:
    """Private helper, không expose qua MCP."""
    ...


def register(mcp):
    """Entry point — register all @mcp.tool() trong module này."""
    @mcp.tool()
    def ten_tool_tieng_viet(tham_so: str) -> str:
        """Mô tả tool 1 câu tiếng Việt.

        GỌI TOOL NÀY KHI người dùng nói: "trigger 1", "trigger 2",
        "trigger 3". Ví dụ cụ thể.

        Args:
            tham_so: Mô tả tham số.
        """
        try:
            data = _helper()
            if not data:
                return "Hiện chưa có dữ liệu."
            return _reply(f"Kết quả: {data}")
        except Exception as e:
            return f"Lỗi: {e}"
```

## Pattern rules (không đàm phán)

### 1. `_reply()` prefix

Mọi tool **thành công** phải wrap response qua `_reply()` từ `tools/_common.py`:

```python
return _reply("Doanh thu tháng 3 là 500 triệu.")
```

`_reply()` prepend ack text để cloud LLM **không** hallucinate "không tìm thấy" trong speculative TTS window.

### 2. Verbose docstring với trigger phrases

Cloud LLM match tool qua docstring. Docstring phải có:

- 1 câu mô tả ngắn
- Dòng `GỌI TOOL NÀY KHI người dùng nói: "...", "...", "..."`
- Trigger phrases tiếng Việt tự nhiên (không formal)
- Ví dụ cụ thể

### 3. Empty data → explicit VN text

Không return `0`, `null`, `[]` thẳng — LLM dễ interpret sai.

```python
# ❌ Sai
return 0

# ✅ Đúng
return "Chưa có đơn hàng nào trong ngày hôm nay."
```

### 4. Error → graceful Vietnamese

**Không throw exception**. Return text explain lỗi:

```python
try:
    resp = urllib.request.urlopen(url, timeout=10)
except Exception as e:
    return f"Không kết nối được đến {_API_URL}. Chi tiết: {e}"
```

### 5. HTTP timeouts bắt buộc

Mọi urllib call phải có `timeout=10`:

```python
urllib.request.urlopen(req, timeout=10)
```

### 6. Tên tool = verb tiếng Việt

- ✅ `lay_doanh_thu`, `them_nhac`, `xoa_file`, `tim_wiki`
- ❌ `revenue`, `add_reminder`, `delete`, `wikipedia_search`

## Env gate pattern

Tool integration cần secret → conditional register trong `server.py`:

```python
if os.getenv("MY_API_KEY"):
    my_module.register(mcp)
```

Boolean flag feature → check `.lower() in ("1", "true", "yes")`:

```python
if os.getenv("ENABLE_PC_CONTROL", "").lower() in ("1", "true", "yes"):
    pc_control.register(mcp)
```

## Security rules

1. **Không hardcode secret** — mọi token qua `os.getenv()`
2. **Không log full token** — nếu cần debug, log prefix 8 char thôi
3. **SQL user input → parametrized** hoặc whitelist regex
4. **File path user input → `Path.resolve()` check** thoát sandbox
5. **HTML input → escape** khi render

## Comments

- **Mặc định không viết comment** — tên function/variable đủ self-documenting
- Chỉ comment khi WHY non-obvious: workaround bug, hidden constraint, invariant surprising
- **Không comment WHAT** code đang làm
- **Không reference task/PR/issue** trong comment

## Testing

- **No test framework set up** hiện tại (project small, tools E2E test qua voice)
- Khi thêm tool phức tạp → viết manual test script trong `plans/{slug}/test-*.py`
- **Không** commit test script vào root

## File naming

- **kebab-case** cho markdown/config (`voice-commands-examples.md`)
- **snake_case** cho Python (`browser_playwright.py`)
- **Descriptive names** — không viết tắt (ví dụ `calendar_gcal.py` không `cal.py`)

## Git conventions

- **Conventional commits:** `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- **No AI references** trong commit message
- **Không commit:** `.env`, `data/*.db`, `data/*.json`, `__pycache__`
