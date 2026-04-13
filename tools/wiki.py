"""Vietnamese Wikipedia lookup."""
import json
import urllib.parse
import urllib.request
from ._common import _reply


def register(mcp):
    @mcp.tool()
    def tim_wiki(tu_khoa: str) -> str:
        """Tra cứu kiến thức từ Wikipedia tiếng Việt (tóm tắt ngắn).

        GỌI TOOL NÀY KHI người dùng hỏi: "X là ai", "X là gì", "nói về X", "giải thích X".
        Ví dụ: "Hồ Chí Minh là ai", "thuyết tương đối là gì", "Einstein là ai".

        Args:
            tu_khoa: chủ đề cần tra cứu (ví dụ "Hồ Chí Minh", "thuyết tương đối")
        """
        query = tu_khoa.strip()
        title = urllib.parse.quote(query.replace(" ", "_"))
        url = f"https://vi.wikipedia.org/api/rest_v1/page/summary/{title}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return f"Wikipedia không có bài viết về '{query}'."
            return f"Lỗi Wikipedia: {e.code}"
        except Exception as e:
            return f"Lỗi tra cứu: {str(e)[:100]}"

        extract = data.get("extract", "")
        if not extract:
            return f"Không có tóm tắt cho '{query}'."
        # Limit to ~500 chars for voice
        if len(extract) > 500:
            extract = extract[:500].rsplit(".", 1)[0] + "."
        return _reply(extract)
