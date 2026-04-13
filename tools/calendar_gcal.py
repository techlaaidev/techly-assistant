"""Google Calendar integration.

Simple mode: set env var GOOGLE_ACCESS_TOKEN (user handles refresh externally).
Tokens expire ~1h; user's refresh system must update the env var.
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from ._common import _reply

try:
    import dateparser
    HAS_DATEPARSER = True
except ImportError:
    HAS_DATEPARSER = False

GCAL_API = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def _get_token() -> str:
    token = os.getenv("GOOGLE_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GOOGLE_ACCESS_TOKEN chưa được cấu hình trong environment.")
    return token


def _gcal_request(method: str, url: str, body: dict | None = None) -> dict:
    token = _get_token()
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _format_event(e: dict) -> str:
    start = e.get("start", {})
    iso = start.get("dateTime") or start.get("date", "")
    summary = e.get("summary", "(không tiêu đề)")
    time_part = iso[11:16] if "T" in iso else "cả ngày"
    return f"- {time_part}: {summary}"


def register(mcp):
    @mcp.tool()
    def xem_lich_hom_nay() -> str:
        """Xem tất cả sự kiện trong Google Calendar hôm nay.

        GỌI TOOL NÀY KHI người dùng hỏi: "lịch hôm nay", "có cuộc hẹn nào hôm nay",
        "meeting hôm nay", "có gì trong lịch hôm nay".
        """
        try:
            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            params = urllib.parse.urlencode({
                "timeMin": start.isoformat().replace("+00:00", "Z"),
                "timeMax": end.isoformat().replace("+00:00", "Z"),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 20,
            })
            data = _gcal_request("GET", f"{GCAL_API}?{params}")
            events = data.get("items", [])
            if not events:
                return _reply("Hôm nay không có sự kiện nào trên lịch.")
            lines = [_format_event(e) for e in events]
            return _reply("Lịch hôm nay:\n" + "\n".join(lines))
        except Exception as e:
            return f"Không truy cập được Google Calendar: {str(e)[:150]}"

    @mcp.tool()
    def xem_lich_trong_tuan() -> str:
        """Xem các sự kiện Google Calendar trong 7 ngày tới.

        GỌI TOOL NÀY KHI người dùng hỏi: "lịch tuần này", "tuần này có gì", "sự kiện sắp tới".
        """
        try:
            now = datetime.now(timezone.utc)
            end = now + timedelta(days=7)
            params = urllib.parse.urlencode({
                "timeMin": now.isoformat().replace("+00:00", "Z"),
                "timeMax": end.isoformat().replace("+00:00", "Z"),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 20,
            })
            data = _gcal_request("GET", f"{GCAL_API}?{params}")
            events = data.get("items", [])
            if not events:
                return _reply("Không có sự kiện nào trong 7 ngày tới.")
            lines = []
            for e in events:
                start = e.get("start", {})
                iso = start.get("dateTime") or start.get("date", "")
                summary = e.get("summary", "(không tiêu đề)")
                day = iso[:10]
                time_part = iso[11:16] if "T" in iso else "cả ngày"
                lines.append(f"- {day} {time_part}: {summary}")
            return _reply("Lịch 7 ngày tới:\n" + "\n".join(lines))
        except Exception as e:
            return f"Không truy cập được Google Calendar: {str(e)[:150]}"

    @mcp.tool()
    def them_su_kien(tieu_de: str, thoi_gian: str, thoi_luong_phut: int = 30) -> str:
        """Thêm sự kiện mới vào Google Calendar.

        GỌI TOOL NÀY KHI người dùng nói: "thêm meeting 3h chiều mai", "lên lịch họp".
        Ví dụ: them_su_kien("Họp với sếp", "3h chiều mai", 60)

        Args:
            tieu_de: tiêu đề sự kiện
            thoi_gian: thời gian tự nhiên VN ("3h chiều mai", "9h sáng thứ 6")
            thoi_luong_phut: thời lượng tính bằng phút (mặc định 30)
        """
        if not HAS_DATEPARSER:
            return "Thiếu dateparser. Chạy: pip install dateparser"
        dt = dateparser.parse(
            thoi_gian,
            languages=["vi", "en"],
            settings={"PREFER_DATES_FROM": "future"},
        )
        if not dt:
            return f"Không hiểu thời gian '{thoi_gian}'."
        if dt.tzinfo is None:
            # Assume local timezone Asia/Bangkok (+07)
            dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))
        end_dt = dt + timedelta(minutes=thoi_luong_phut)
        body = {
            "summary": tieu_de,
            "start": {"dateTime": dt.isoformat(), "timeZone": "Asia/Bangkok"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Bangkok"},
        }
        try:
            _gcal_request("POST", GCAL_API, body)
            return (
                f"Đã thêm sự kiện '{tieu_de}' vào lúc "
                f"{dt.strftime('%H:%M ngày %d/%m/%Y')} "
                f"(kéo dài {thoi_luong_phut} phút)."
            )
        except Exception as e:
            return f"Không thêm được sự kiện: {str(e)[:150]}"
