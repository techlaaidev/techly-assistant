"""Brave Search web search.

Requires env: BRAVE_API_KEY
Free tier: 2000 queries/month at https://api.search.brave.com/
"""
import json
import os
import urllib.parse
import urllib.request
from ._common import _reply

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"


def register(mcp):
    @mcp.tool()
    def tim_kiem_web(tu_khoa: str, so_ket_qua: int = 5) -> str:
        """Tìm kiếm trên web (Brave Search). Trả về danh sách title + snippet.

        GỌI TOOL NÀY KHI người dùng hỏi: "tìm trên web về X", "search Google X",
        "tìm thông tin X trên mạng".
        Ví dụ: "tìm trên web về Vingroup", "search news AI 2026".

        Args:
            tu_khoa: từ khóa tìm kiếm
            so_ket_qua: số kết quả (1-10, mặc định 5)
        """
        if not BRAVE_API_KEY:
            return "Brave Search chưa được cấu hình. Set BRAVE_API_KEY trong .env"
        params = urllib.parse.urlencode({
            "q": tu_khoa,
            "count": max(1, min(so_ket_qua, 10)),
        })
        req = urllib.request.Request(
            f"{BRAVE_URL}?{params}",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY,
                "User-Agent": "Techly-Assistant/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return f"Lỗi tìm kiếm: {str(e)[:120]}"

        results = data.get("web", {}).get("results", [])
        if not results:
            return f"Không có kết quả cho '{tu_khoa}'."
        lines = []
        for i, r in enumerate(results[:so_ket_qua], 1):
            title = r.get("title", "(no title)")
            desc = r.get("description", "")[:200]
            lines.append(f"{i}. {title}\n   {desc}")
        return _reply("\n\n".join(lines))
