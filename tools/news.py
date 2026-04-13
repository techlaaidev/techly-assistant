"""Vietnamese news aggregator via RSS feeds."""
import urllib.request
import xml.etree.ElementTree as ET
from ._common import _reply

_FEEDS = {
    "vnexpress": "https://vnexpress.net/rss/tin-moi-nhat.rss",
    "tuoi tre": "https://tuoitre.vn/rss/tin-moi-nhat.rss",
    "thanh nien": "https://thanhnien.vn/rss/home.rss",
    "vietnamnet": "https://vietnamnet.vn/rss/home.rss",
}


def _parse_rss(url: str, limit: int = 5) -> list:
    """Fetch RSS and return list of (title, link) tuples."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []
    items = []
    for item in root.iter("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        if title_el is not None and title_el.text:
            items.append((title_el.text.strip(),
                          link_el.text.strip() if link_el is not None and link_el.text else ""))
        if len(items) >= limit:
            break
    return items


def register(mcp):
    @mcp.tool()
    def lay_tin_moi_nhat() -> str:
        """Trả về 5 tin tức mới nhất từ các báo lớn Việt Nam (VnExpress, Tuổi Trẻ, Thanh Niên).

        GỌI TOOL NÀY KHI người dùng hỏi: "tin mới", "tin tức hôm nay", "có tin gì mới không", "đọc tin".
        """
        all_headlines = []
        for source, url in _FEEDS.items():
            items = _parse_rss(url, limit=2)
            for title, _ in items:
                all_headlines.append(f"[{source.title()}] {title}")
            if len(all_headlines) >= 5:
                break
        if not all_headlines:
            return "Không lấy được tin tức lúc này. Vui lòng thử lại sau."
        output = "\n".join(f"{i+1}. {h}" for i, h in enumerate(all_headlines[:5]))
        return _reply(output)

    @mcp.tool()
    def doc_bao(nguon: str = "vnexpress") -> str:
        """Trả về 5 tin mới nhất từ một nguồn báo cụ thể.

        GỌI TOOL NÀY KHI người dùng hỏi: "tin VnExpress", "báo Tuổi Trẻ", "đọc Thanh Niên".
        Args:
            nguon: tên nguồn - vnexpress | tuoi tre | thanh nien | vietnamnet
        """
        key = nguon.lower().strip()
        if key not in _FEEDS:
            return f"Không hỗ trợ nguồn '{nguon}'. Các nguồn: {', '.join(_FEEDS.keys())}"
        items = _parse_rss(_FEEDS[key], limit=5)
        if not items:
            return f"Không lấy được tin từ {nguon}."
        output = "\n".join(f"{i+1}. {title}" for i, (title, _) in enumerate(items))
        return _reply(output)
