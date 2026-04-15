"""Proactive scheduler — timed notifications via Telegram.

Works around Xiaozhi pull-only MCP by using Telegram as the proactive
channel. BackgroundScheduler runs in-process with the MCP server.

Requires:
    pip install apscheduler
    ENABLE_SCHEDULER=1 in .env
    TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env

Skeleton note: uses in-memory jobstore — scheduled jobs are lost on
server restart. Upgrade to SQLAlchemyJobStore for persistence later.
"""
import atexit
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from ._common import _reply

_scheduler: BackgroundScheduler | None = None
_TZ = os.getenv("SCHEDULER_TZ", "Asia/Bangkok")


def _safe_shutdown() -> None:
    """Shutdown guard — atexit may fire after manual shutdown in tests."""
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)


def _get_scheduler() -> BackgroundScheduler:
    """Lazy singleton — start on first tool call, not module import."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone=_TZ)
        _scheduler.start()
        atexit.register(_safe_shutdown)
    return _scheduler


def _push_telegram(noi_dung: str) -> None:
    """Send proactive notification via Telegram Bot API.

    Top-level function (not closure) so APScheduler can reference it
    cleanly without pickling issues if jobstore upgraded later.
    Runs in scheduler thread — fail silent to avoid crashing the loop.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": f"[Techly] {noi_dung}",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def register(mcp):
    @mcp.tool()
    def dat_lich_nhac_chu_dong(noi_dung: str, sau_phut: int) -> str:
        """Đặt lịch gửi thông báo chủ động qua Telegram sau N phút.

        GỌI TOOL NÀY KHI người dùng nói: "nhắc tôi X sau 30 phút",
        "thông báo cho tôi X sau N phút", "đặt lịch nhắc X sau...".
        Khác với reminder thường: tool này tự đẩy thông báo xuống điện
        thoại qua Telegram, không cần user hỏi lại.

        Args:
            noi_dung: Nội dung thông báo sẽ gửi
            sau_phut: Số phút từ bây giờ (1 - 10080)
        """
        if sau_phut < 1 or sau_phut > 10080:
            return "Thời gian phải từ 1 phút tới 10080 phút (1 tuần)."
        if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
            return (
                "Chưa cấu hình Telegram. "
                "Set TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong .env."
            )
        sched = _get_scheduler()
        run_at = datetime.now() + timedelta(minutes=sau_phut)
        job = sched.add_job(
            _push_telegram,
            trigger=DateTrigger(run_date=run_at, timezone=_TZ),
            args=[noi_dung],
            name=noi_dung[:50],
            replace_existing=False,
        )
        return _reply(
            f"Đã đặt lịch nhắc lúc {run_at.strftime('%H:%M ngày %d/%m')}. "
            f"Mã lịch: {job.id[:8]}"
        )

    @mcp.tool()
    def xem_lich_nhac_chu_dong() -> str:
        """Xem các lịch nhắc chủ động đang chờ.

        GỌI TOOL NÀY KHI người dùng hỏi: "có nhắc nhở nào không",
        "lịch nhắc chủ động đang chờ", "xem các thông báo đã đặt".
        """
        sched = _get_scheduler()
        jobs = sched.get_jobs()
        if not jobs:
            return "Không có lịch nhắc chủ động nào đang chờ."
        lines = []
        for j in jobs[:20]:
            run_at = j.next_run_time
            when = run_at.strftime("%H:%M %d/%m") if run_at else "?"
            lines.append(f"- [{j.id[:8]}] {when} — {j.name}")
        return _reply("Lịch nhắc chủ động:\n" + "\n".join(lines))

    @mcp.tool()
    def xoa_lich_nhac_chu_dong(ma_lich: str) -> str:
        """Xóa lịch nhắc chủ động theo mã.

        GỌI TOOL NÀY KHI người dùng nói: "hủy lịch nhắc X",
        "xóa thông báo Y", "bỏ lịch nhắc...".

        Args:
            ma_lich: Mã lịch (8 ký tự đầu) lấy từ xem_lich_nhac_chu_dong
        """
        sched = _get_scheduler()
        for j in sched.get_jobs():
            if j.id.startswith(ma_lich):
                j.remove()
                return _reply(f"Đã xóa lịch nhắc {ma_lich}.")
        return f"Không tìm thấy lịch nhắc có mã bắt đầu bằng {ma_lich}."
