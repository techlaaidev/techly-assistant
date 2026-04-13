"""Time-based reminders with natural-language Vietnamese parsing."""
import json
from datetime import datetime, timedelta
from ._common import _reply, REMINDERS_FILE

try:
    import dateparser
    HAS_DATEPARSER = True
except ImportError:
    HAS_DATEPARSER = False


def _load_reminders() -> list:
    if not REMINDERS_FILE.exists():
        return []
    try:
        return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_reminders(reminders: list) -> None:
    REMINDERS_FILE.write_text(
        json.dumps(reminders, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse_vn_time(text: str) -> datetime | None:
    """Parse Vietnamese time expressions to datetime."""
    text = text.lower().strip()
    now = datetime.now()

    # Handle simple "X phút nữa" / "X giờ nữa"
    if "phút nữa" in text or "phut nua" in text:
        try:
            mins = int("".join(c for c in text if c.isdigit()))
            return now + timedelta(minutes=mins)
        except ValueError:
            pass
    if "giờ nữa" in text or "gio nua" in text:
        try:
            hours = int("".join(c for c in text if c.isdigit()))
            return now + timedelta(hours=hours)
        except ValueError:
            pass

    if HAS_DATEPARSER:
        dt = dateparser.parse(
            text,
            languages=["vi", "en"],
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now},
        )
        if dt:
            return dt
    return None


def register(mcp):
    @mcp.tool()
    def them_nhac(thoi_gian: str, noi_dung: str) -> str:
        """Thêm một lời nhắc mới có thời gian cụ thể.

        GỌI TOOL NÀY KHI người dùng nói: "nhắc tôi X vào thời gian Y", "ghi nhớ Y làm X".
        Ví dụ: "nhắc tôi 3h chiều mai họp" → them_nhac("3h chiều mai", "họp").
        Ví dụ: "nhắc 20 phút nữa uống nước" → them_nhac("20 phút nữa", "uống nước").

        Args:
            thoi_gian: mô tả thời gian tự nhiên (vd "3h chiều mai", "20 phút nữa")
            noi_dung: việc cần nhắc
        """
        dt = _parse_vn_time(thoi_gian)
        if not dt:
            return f"Không hiểu thời gian '{thoi_gian}'. Thử lại với dạng '3h chiều mai' hoặc '20 phút nữa'."
        reminders = _load_reminders()
        new_id = max((r.get("id", 0) for r in reminders), default=0) + 1
        reminders.append({
            "id": new_id,
            "time_iso": dt.isoformat(),
            "content": noi_dung,
            "created_at": datetime.now().isoformat(),
        })
        _save_reminders(reminders)
        return (
            f"Đã lưu nhắc số {new_id}: "
            f"{dt.strftime('%H:%M ngày %d/%m/%Y')} - {noi_dung}"
        )

    @mcp.tool()
    def xem_nhac_sap_toi() -> str:
        """Xem danh sách các lời nhắc sắp tới (chưa qua thời điểm).

        GỌI TOOL NÀY KHI người dùng hỏi: "có nhắc gì không", "nhắc sắp tới", "xem các lời nhắc".
        """
        reminders = _load_reminders()
        now = datetime.now()
        upcoming = [
            r for r in reminders
            if datetime.fromisoformat(r["time_iso"]) > now
        ]
        upcoming.sort(key=lambda r: r["time_iso"])
        if not upcoming:
            return _reply("Hiện không có lời nhắc nào sắp tới.")
        lines = []
        for r in upcoming[:10]:
            dt = datetime.fromisoformat(r["time_iso"])
            lines.append(
                f"#{r['id']}: {dt.strftime('%H:%M ngày %d/%m')} - {r['content']}"
            )
        return _reply("\n".join(lines))

    @mcp.tool()
    def xoa_nhac(id: int) -> str:
        """Xóa một lời nhắc theo số thứ tự.

        GỌI TOOL NÀY KHI người dùng nói: "xóa nhắc số X", "bỏ lời nhắc số Y".
        Args:
            id: số thứ tự của lời nhắc (lấy từ xem_nhac_sap_toi)
        """
        reminders = _load_reminders()
        before = len(reminders)
        reminders = [r for r in reminders if r.get("id") != id]
        if len(reminders) == before:
            return f"Không có lời nhắc số {id}."
        _save_reminders(reminders)
        return f"Đã xóa lời nhắc số {id}."
