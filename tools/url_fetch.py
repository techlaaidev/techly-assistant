"""Fetch a URL and return cleaned text content (no external deps).

Self-hosted alternative to Firecrawl. Uses urllib + simple HTML stripping.
"""
import re
import urllib.request
from ._common import _reply


def _strip_html(html: str) -> str:
    """Very simple HTML to text. Remove scripts/styles, then tags."""
    # Remove script and style blocks
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    text = (text.replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&#39;", "'"))
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def register(mcp):
    @mcp.tool()
    def doc_trang_web(url: str, max_chars: int = 1500) -> str:
        """Tải một URL và trả về nội dung text đã được làm sạch (loại bỏ HTML).

        GỌI TOOL NÀY KHI người dùng nói: "đọc trang web X", "tóm tắt URL Y",
        "xem nội dung của link Z".

        Args:
            url: URL đầy đủ (https://...)
            max_chars: giới hạn ký tự trả về (mặc định 1500)
        """
        if not url.startswith(("http://", "https://")):
            return "URL phải bắt đầu bằng http:// hoặc https://"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Techly-Assistant)"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                ctype = resp.headers.get("Content-Type", "")
                raw = resp.read()
                if len(raw) > 1_000_000:
                    return "Trang web quá lớn (>1MB)."
                content = raw.decode("utf-8", errors="replace")
        except Exception as e:
            return f"Không tải được URL: {str(e)[:150]}"

        if "html" in ctype.lower():
            text = _strip_html(content)
        else:
            text = content
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        return _reply(f"Nội dung từ {url}:\n\n{text}")
