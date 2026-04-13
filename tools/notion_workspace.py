"""Notion workspace integration via REST API.

Requires env:
    NOTION_TOKEN  - Internal integration token from notion.so/my-integrations
"""
import json
import os
import urllib.request
from ._common import _reply

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _notion_request(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{NOTION_API}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_title(page: dict) -> str:
    """Try to extract page title from Notion page object."""
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            title_arr = prop.get("title", [])
            if title_arr:
                return "".join(t.get("plain_text", "") for t in title_arr)
    return "(không tiêu đề)"


def register(mcp):
    @mcp.tool()
    def tim_trong_notion(tu_khoa: str) -> str:
        """Tìm pages/databases trong Notion workspace bằng từ khóa.

        GỌI TOOL NÀY KHI người dùng hỏi: "tìm trong Notion về X", "Notion có gì về Y".

        Args:
            tu_khoa: từ khóa cần tìm
        """
        if not NOTION_TOKEN:
            return "Notion chưa cấu hình. Set NOTION_TOKEN trong .env"
        try:
            data = _notion_request("POST", "/search", {
                "query": tu_khoa,
                "page_size": 10,
            })
            results = data.get("results", [])
            if not results:
                return f"Không tìm thấy gì về '{tu_khoa}' trong Notion."
            lines = []
            for r in results[:5]:
                title = _extract_title(r)
                obj_type = r.get("object", "")
                lines.append(f"- [{obj_type}] {title}")
            return _reply(f"Notion tìm thấy {len(results)} kết quả:\n" + "\n".join(lines))
        except Exception as e:
            return f"Lỗi Notion: {str(e)[:150]}"
