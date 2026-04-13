"""Local knowledge base search (grep-based, Vietnamese-aware)."""
import re
from ._common import _reply, KB_DIR

_STOPWORDS = {
    "là", "gì", "thế", "nào", "làm", "sao", "của", "cho", "tôi", "bạn",
    "ai", "có", "không", "và", "hay", "thì", "ở", "đâu", "khi", "vì",
    "để", "mà", "với", "trong", "ra", "được", "một", "các", "những",
    "the", "a", "an", "is", "are", "what", "how", "why", "when", "where",
}


def _extract_keywords(question: str) -> list:
    """Strip stopwords, return content words only."""
    words = re.findall(r"\w+", question.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _score_paragraph(para: str, keywords: list) -> int:
    low = para.lower()
    return sum(low.count(kw) for kw in keywords)


def register(mcp):
    @mcp.tool()
    def tim_trong_tai_lieu(cau_hoi: str) -> str:
        """Tìm câu trả lời trong kho tài liệu nội bộ Techla AI.

        GỌI TOOL NÀY KHI người dùng hỏi về: quy trình, chính sách, hướng dẫn nội bộ,
        thủ tục công ty, tài liệu kỹ thuật, quy định công ty.
        Ví dụ: "chính sách nghỉ phép", "quy trình onboarding", "cách setup ESP32".

        Args:
            cau_hoi: câu hỏi đầy đủ từ người dùng
        """
        if not KB_DIR.exists() or not any(KB_DIR.glob("*.md")):
            return "Kho tài liệu chưa có file nào. Vui lòng thêm file .md vào data/knowledge_base/"

        keywords = _extract_keywords(cau_hoi)
        if not keywords:
            return "Không hiểu câu hỏi. Vui lòng diễn đạt rõ hơn."

        results = []
        for md_file in KB_DIR.glob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
                score = _score_paragraph(para, keywords)
                if score > 0:
                    results.append((score, md_file.stem, para))

        if not results:
            return f"Không tìm thấy thông tin về '{cau_hoi}' trong tài liệu."

        results.sort(key=lambda x: -x[0])
        top = results[:3]
        output = "\n\n".join(
            f"[{src}]\n{para[:400]}"
            for _, src, para in top
        )
        return _reply(output)

    @mcp.tool()
    def liet_ke_tai_lieu() -> str:
        """Liệt kê tên các tài liệu trong kho kiến thức nội bộ.

        GỌI TOOL NÀY KHI người dùng hỏi: "có những tài liệu gì", "list tài liệu",
        "kho tri thức có gì".
        """
        if not KB_DIR.exists():
            return "Kho tài liệu chưa được tạo."
        files = sorted(KB_DIR.glob("*.md"))
        if not files:
            return "Kho tài liệu đang trống."
        names = [f.stem.replace("-", " ").replace("_", " ") for f in files]
        return _reply("Các tài liệu hiện có:\n" + "\n".join(f"- {n}" for n in names))
