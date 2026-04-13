"""Telegram Bot integration via Bot API.

Requires env:
    TELEGRAM_BOT_TOKEN  - from BotFather
    TELEGRAM_CHAT_ID    - default chat ID to send to
"""
import json
import os
import urllib.parse
import urllib.request
from ._common import _reply

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_DEFAULT_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
TG_API = "https://api.telegram.org"


def _tg_request(method: str, params: dict) -> dict:
    url = f"{TG_API}/bot{TG_TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def register(mcp):
    @mcp.tool()
    def gui_telegram(noi_dung: str, chat_id: str = "") -> str:
        """Gửi tin nhắn tới Telegram chat (cá nhân hoặc nhóm).

        GỌI TOOL NÀY KHI người dùng nói: "gửi Telegram X", "thông báo qua Telegram Y",
        "nhắn cho team trên Telegram".

        Args:
            noi_dung: nội dung tin nhắn
            chat_id: chat ID (mặc định TELEGRAM_CHAT_ID)
        """
        if not TG_TOKEN:
            return "Telegram chưa cấu hình. Set TELEGRAM_BOT_TOKEN trong .env"
        target = chat_id or TG_DEFAULT_CHAT
        if not target:
            return "Chưa có chat ID. Set TELEGRAM_CHAT_ID trong .env hoặc truyền tham số."
        try:
            res = _tg_request("sendMessage", {
                "chat_id": target,
                "text": noi_dung,
            })
            if not res.get("ok"):
                return f"Lỗi Telegram: {res.get('description', 'unknown')}"
            return f"Đã gửi tin nhắn Telegram tới {target}."
        except Exception as e:
            return f"Lỗi Telegram: {str(e)[:150]}"

    @mcp.tool()
    def doc_tin_nhan_telegram(so_luong: int = 5) -> str:
        """Đọc các update mới nhất từ Telegram bot (tin nhắn người dùng gửi tới bot).

        GỌI TOOL NÀY KHI người dùng hỏi: "Telegram có gì mới", "tin nhắn bot mới".
        """
        if not TG_TOKEN:
            return "Telegram chưa cấu hình."
        try:
            res = _tg_request("getUpdates", {"limit": max(1, min(so_luong, 20))})
            if not res.get("ok"):
                return f"Lỗi Telegram: {res.get('description', 'unknown')}"
            updates = res.get("result", [])
            if not updates:
                return "Không có tin nhắn mới."
            lines = []
            for u in updates[-so_luong:]:
                msg = u.get("message", {})
                user = msg.get("from", {}).get("username") or msg.get("from", {}).get("first_name", "?")
                text = msg.get("text", "")[:200]
                lines.append(f"@{user}: {text}")
            return _reply("Tin nhắn Telegram gần nhất:\n" + "\n".join(lines))
        except Exception as e:
            return f"Lỗi Telegram: {str(e)[:150]}"
