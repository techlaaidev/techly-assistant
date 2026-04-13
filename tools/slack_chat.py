"""Slack messaging via Bot API.

Requires env:
    SLACK_BOT_TOKEN     - xoxb-... bot token
    SLACK_DEFAULT_CHANNEL - default channel ID hoặc tên (vd "#general")
"""
import json
import os
import urllib.parse
import urllib.request
from ._common import _reply

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_DEFAULT_CHANNEL = os.getenv("SLACK_DEFAULT_CHANNEL", "#general")
SLACK_API = "https://slack.com/api"


def _slack_request(method: str, body: dict | None = None) -> dict:
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        }
        req = urllib.request.Request(f"{SLACK_API}/{method}", data=data, headers=headers)
    else:
        headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        req = urllib.request.Request(f"{SLACK_API}/{method}", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def register(mcp):
    @mcp.tool()
    def gui_tin_nhan_slack(noi_dung: str, kenh: str = "") -> str:
        """Gửi tin nhắn vào Slack channel.

        GỌI TOOL NÀY KHI người dùng nói: "post Slack X", "gửi Slack 'meeting 3h'",
        "thông báo team trên Slack".

        Args:
            noi_dung: nội dung tin nhắn
            kenh: channel ID hoặc tên (mặc định SLACK_DEFAULT_CHANNEL)
        """
        if not SLACK_BOT_TOKEN:
            return "Slack chưa cấu hình. Set SLACK_BOT_TOKEN trong .env"
        target = kenh or SLACK_DEFAULT_CHANNEL
        try:
            res = _slack_request("chat.postMessage", {
                "channel": target,
                "text": noi_dung,
            })
            if not res.get("ok"):
                return f"Lỗi Slack: {res.get('error', 'unknown')}"
            return f"Đã gửi tin nhắn vào {target}."
        except Exception as e:
            return f"Lỗi Slack: {str(e)[:150]}"

    @mcp.tool()
    def doc_tin_nhan_slack_gan_day(kenh: str = "", so_luong: int = 5) -> str:
        """Đọc các tin nhắn mới nhất trong Slack channel.

        GỌI TOOL NÀY KHI người dùng hỏi: "Slack có gì mới", "tin nhắn mới trong channel X".
        """
        if not SLACK_BOT_TOKEN:
            return "Slack chưa cấu hình."
        target = kenh or SLACK_DEFAULT_CHANNEL
        try:
            res = _slack_request("conversations.history", {
                "channel": target,
                "limit": max(1, min(so_luong, 20)),
            })
            if not res.get("ok"):
                return f"Lỗi Slack: {res.get('error', 'unknown')}"
            messages = res.get("messages", [])
            if not messages:
                return f"Channel {target} chưa có tin nhắn."
            lines = []
            for m in messages[:so_luong]:
                user = m.get("user", "?")
                text = m.get("text", "")[:200]
                lines.append(f"@{user}: {text}")
            return _reply(f"Tin nhắn gần nhất trong {target}:\n" + "\n".join(lines))
        except Exception as e:
            return f"Lỗi Slack: {str(e)[:150]}"
