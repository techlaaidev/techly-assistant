---
phase: 5
title: Knowledge base search — local docs RAG
status: pending
effort: 2h
priority: high
---

# Phase 5: Knowledge Base RAG

## Context
Highest value cho Techla AI — cho phép voice query trên docs nội bộ (quy trình, chính sách, technical docs). Dùng grep-based search trước, upgrade lên embedding sau nếu cần.

## Features

### 5.1 Search knowledge base
**Tool:** `tim_trong_tai_lieu(cau_hoi: str)` — semantic-ish grep

### 5.2 List documents
**Tool:** `liet_ke_tai_lieu()` — list filenames in KB

## Storage

```
data/knowledge_base/
├── chinh-sach-nghi-phep.md
├── quy-trinh-onboarding.md
├── technical-esp32-setup.md
└── ...
```

Tất cả `.md` files, user tự thêm/sửa.

## Implementation: Simple grep v1 (recommended start)

```python
from pathlib import Path
import re
from ._common import _reply, BASE_DIR

KB_DIR = BASE_DIR / "data" / "knowledge_base"

def _extract_keywords(question: str) -> list[str]:
    """Extract meaningful keywords, strip stopwords."""
    stopwords = {"là", "gì", "thế", "nào", "làm", "sao", "của", "cho", "tôi",
                 "bạn", "ai", "có", "không", "và", "hay", "thì"}
    words = re.findall(r'\w+', question.lower())
    return [w for w in words if w not in stopwords and len(w) > 1]

def _score_paragraph(para: str, keywords: list[str]) -> int:
    para_lower = para.lower()
    return sum(1 for kw in keywords if kw in para_lower)

def register(mcp):
    @mcp.tool()
    def tim_trong_tai_lieu(cau_hoi: str) -> str:
        """Tìm câu trả lời trong kho tài liệu nội bộ Techla AI.

        GỌI TOOL NÀY KHI người dùng hỏi về: quy trình, chính sách, hướng dẫn nội bộ,
        thủ tục công ty, tài liệu kỹ thuật, quy định.
        Ví dụ: "chính sách nghỉ phép", "quy trình onboarding", "cách setup ESP32".

        Args:
            cau_hoi: Câu hỏi đầy đủ từ người dùng
        """
        if not KB_DIR.exists():
            return "Kho tài liệu chưa được tạo. Vui lòng thêm file .md vào data/knowledge_base/"

        keywords = _extract_keywords(cau_hoi)
        if not keywords:
            return "Không hiểu câu hỏi. Vui lòng diễn đạt rõ hơn."

        results = []
        for md_file in KB_DIR.glob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            # Split by paragraph
            paras = [p.strip() for p in text.split("\n\n") if p.strip()]
            for para in paras:
                score = _score_paragraph(para, keywords)
                if score > 0:
                    results.append((score, md_file.stem, para))

        if not results:
            return f"Không tìm thấy thông tin về '{cau_hoi}' trong tài liệu."

        results.sort(key=lambda x: -x[0])
        top = results[:3]
        output = "\n\n".join(
            f"[{src}]\n{para[:400]}"
            for score, src, para in top
        )
        return _reply(output)

    @mcp.tool()
    def liet_ke_tai_lieu() -> str:
        """Liệt kê tên các tài liệu có trong kho kiến thức nội bộ."""
        if not KB_DIR.exists():
            return "Kho tài liệu chưa được tạo."
        files = sorted(KB_DIR.glob("*.md"))
        if not files:
            return "Kho tài liệu trống."
        names = [f.stem.replace("-", " ") for f in files]
        return _reply("Các tài liệu hiện có:\n" + "\n".join(f"- {n}" for n in names))
```

## Upgrade path v2 (optional, nếu v1 quá yếu)

- Dùng `sentence-transformers` + FAISS index
- Model: `intfloat/multilingual-e5-small` (~100MB, hỗ trợ VN)
- Pre-compute embeddings on startup
- Cosine similarity search

```python
# pseudo
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('intfloat/multilingual-e5-small')
# Load .md files → chunk → embed → store in numpy array
# Query: embed question → dot product → top-K
```

Chỉ upgrade khi v1 không đủ tốt. YAGNI.

## Seed content (user tự thêm sau)

Tạo vài file mẫu để test:
- `data/knowledge_base/README.md` — giải thích cách dùng
- `data/knowledge_base/chinh-sach-nghi-phep.md` — sample policy doc
- `data/knowledge_base/quy-trinh-onboarding.md` — sample process doc

## Todo

- [ ] Create `data/knowledge_base/` directory
- [ ] Seed 2-3 sample .md files (short, Vietnamese)
- [ ] Create `tools/kb_search.py` với grep v1 implementation
- [ ] Register in `server.py`
- [ ] Voice test: "chính sách nghỉ phép", "quy trình onboarding"
- [ ] Evaluate: nếu accuracy tệ → upgrade v2 embedding

## Success criteria

- Tools callable via voice
- Return top 3 most relevant paragraphs
- Handle empty/missing KB gracefully
- Response < 1 second for KB < 100 files

## Risks

- Grep naive → miss semantic matches → upgrade v2 nếu cần
- Paragraphs quá dài → truncate to 400 chars (fit voice)
- User hỏi quá mơ hồ → fallback "không tìm thấy"
