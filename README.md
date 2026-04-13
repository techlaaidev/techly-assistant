# Techly Assistant

MCP server cung cấp custom tools tiếng Việt cho voice assistant Xiaozhi (ESP32-S3 + cloud).

Bridge giữa Xiaozhi cloud (WebSocket) ↔ stdio MCP server với 28+ tools cho business + personal use.

## Architecture

```
ESP32 (mic/loa) ↔ Xiaozhi cloud (ASR/LLM/TTS) ↔ MCP endpoint WebSocket
                                                        ↓
                                              mcp_pipe.py (bridge)
                                                        ↓
                                              server.py (FastMCP stdio)
                                                        ↓
                                              tools/ (Vietnamese tools)
```

## Tools (28+)

| Category | Tools |
|---|---|
| **Company** | doanh thu, đơn hàng, thông tin công ty, khách VIP, sản phẩm bán chạy, lịch họp |
| **Time** | giờ hiện tại |
| **Weather** | thời tiết VN (open-meteo, no key) |
| **Notes** | ghi chú / đọc / xóa |
| **Calculator** | tính toán an toàn |
| **News** | tin mới VnExpress / Tuổi Trẻ / Thanh Niên / VietnamNet |
| **Finance** | tỷ giá, giá vàng SJC, giá cổ phiếu VN, VN-Index |
| **Wiki** | tra cứu Wikipedia tiếng Việt |
| **Translate** | VN ↔ EN (MyMemory free) |
| **Reminder** | nhắc có thời gian (parse VN tự nhiên) |
| **Expense** | ghi chi tiêu, tổng tháng, báo cáo |
| **KB Search** | tìm trong tài liệu nội bộ |
| **Smart Home** *(optional)* | Home Assistant REST (đèn, điều hoà, công tắc) |
| **Calendar** *(optional)* | Google Calendar (lịch hôm nay, thêm event) |

## Setup

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
# Edit .env, fill in:
#   XIAOZHI_MCP_WSS  (required, từ xiaozhi.me agent)
#   HA_URL, HA_TOKEN (optional, Home Assistant)
#   GOOGLE_ACCESS_TOKEN (optional, Google Calendar)
```

### 3. Run

```bash
python mcp_pipe.py
```

Bridge spawns `server.py` as stdio subprocess and connects to Xiaozhi cloud.

## Project structure

```
.
├── server.py              # MCP entry point, registers all tools
├── mcp_pipe.py            # WebSocket bridge xiaozhi.me ↔ stdio
├── tools/                 # 1 file per feature
│   ├── _common.py         # shared helpers (_reply, _read_company_section)
│   ├── company.py
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
│   ├── home_assistant.py  # conditional on HA_URL+HA_TOKEN
│   └── calendar_gcal.py   # conditional on GOOGLE_ACCESS_TOKEN
├── data/
│   ├── knowledge_base/    # local docs for kb_search tool
│   ├── expenses.db        # auto, gitignored
│   ├── reminders.json     # auto, gitignored
│   └── notes.txt          # auto, gitignored
├── company_data.md        # company info read by company.py tools
├── docs/
│   └── xiaozhi-agent-system-prompt.md  # paste into xiaozhi.me dashboard
├── plans/                 # implementation plans
└── .env                   # secrets, gitignored
```

## Tool design pattern

Mỗi tool follow pattern:
1. **`_reply()` prefix** — prepend ack text "Đã lấy thông tin thành công..." để LLM cloud không hallucinate "không tìm thấy"
2. **Verbose docstring** với "GỌI TOOL NÀY KHI..." + ví dụ trigger phrases
3. **Empty data → explicit "chưa có" message** thay vì 0/null
4. **Error → graceful Vietnamese message**

Example: `tools/company.py`

```python
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
2. Import + register trong `server.py`
3. Restart `mcp_pipe.py`
4. Cloud LLM tự discovery tool qua `tools/list` MCP request

## Security

- `.env` chứa secrets (token, API keys) — **đã gitignored**
- `mcp_pipe.py` đọc `XIAOZHI_MCP_WSS` từ env, không hardcode
- Calculator dùng whitelist regex thay vì raw `eval()`
- HTTP calls có timeout 10s + try/except wrap

## License

Internal use - Techla AI
