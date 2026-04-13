"""Apify Actor runner — call any of 4000+ Apify Actors.

Requires env: APIFY_TOKEN
Free tier credits at https://apify.com/
"""
import json
import os
import time
import urllib.parse
import urllib.request
from ._common import _reply

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
APIFY_BASE = "https://api.apify.com/v2"


def _apify_call(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{APIFY_BASE}{path}?token={APIFY_TOKEN}"
    req = urllib.request.Request(
        url,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def register(mcp):
    @mcp.tool()
    def chay_apify_actor(actor_id: str, input_json: str = "{}") -> str:
        """Chạy một Apify Actor và trả về kết quả (synchronous mode).

        GỌI TOOL NÀY KHI cần scrape data từ web không có sẵn API.
        Ví dụ Actor IDs phổ biến:
        - apify/google-search-scraper - scrape Google search
        - apify/instagram-scraper - scrape Instagram posts
        - compass/crawler-google-places - scrape Google Maps
        - apify/website-content-crawler - generic web crawler

        Args:
            actor_id: ID actor dạng "user/name" (vd "apify/google-search-scraper")
            input_json: JSON string chứa input của actor (vd '{"queries":"phở Hà Nội"}')
        """
        if not APIFY_TOKEN:
            return "Apify chưa được cấu hình. Set APIFY_TOKEN trong .env"
        try:
            payload = json.loads(input_json) if input_json else {}
        except json.JSONDecodeError as e:
            return f"input_json không hợp lệ: {e}"

        actor_path = actor_id.replace("/", "~")
        try:
            run = _apify_call("POST", f"/acts/{actor_path}/run-sync-get-dataset-items", payload)
            if isinstance(run, list):
                items = run
            elif isinstance(run, dict):
                items = run.get("data", [])
            else:
                items = []
            if not items:
                return f"Actor {actor_id} không trả về dữ liệu."
            preview = items[:5]
            return _reply(
                f"Actor {actor_id} trả về {len(items)} items. Preview 5 items đầu:\n\n"
                + json.dumps(preview, ensure_ascii=False, indent=2)[:2000]
            )
        except Exception as e:
            return f"Lỗi chạy Actor: {str(e)[:200]}"

    @mcp.tool()
    def tim_kiem_google_apify(tu_khoa: str) -> str:
        """Tìm kiếm Google qua Apify Google Search Scraper.

        GỌI TOOL NÀY KHI: cần search Google chi tiết, "search Google về X".
        """
        return chay_apify_actor(
            "apify/google-search-scraper",
            json.dumps({"queries": tu_khoa, "maxPagesPerQuery": 1}),
        )
