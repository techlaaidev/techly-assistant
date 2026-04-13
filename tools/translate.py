"""Translation tool using MyMemory free API (no key, 5000 chars/day)."""
import json
import urllib.parse
import urllib.request
from ._common import _reply


def register(mcp):
    @mcp.tool()
    def dich(text: str, sang: str = "en") -> str:
        """Dịch một đoạn văn bản từ tiếng Việt sang ngôn ngữ khác (mặc định tiếng Anh).

        GỌI TOOL NÀY KHI người dùng nói: "dịch X sang tiếng Anh", "nghĩa tiếng Anh của X",
        "X trong tiếng Anh là gì".
        Ví dụ: "dịch chào buổi sáng sang tiếng Anh", "good morning trong tiếng Việt là gì".

        Args:
            text: đoạn văn cần dịch
            sang: mã ngôn ngữ đích ("en", "ja", "ko", "zh", "fr"). Mặc định "en".
        """
        src = "vi"
        tgt = sang.lower().strip()
        # Auto-detect: nếu chứa ký tự ASCII-only, có thể là EN → dịch sang VI
        if all(ord(c) < 128 for c in text):
            src, tgt = "en", "vi"
        pair = f"{src}|{tgt}"
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={pair}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText", "")
            if not translated:
                return "Không dịch được đoạn văn này."
            return _reply(f'"{text}" dịch thành: {translated}')
        except Exception as e:
            return f"Lỗi dịch thuật: {str(e)[:100]}"
