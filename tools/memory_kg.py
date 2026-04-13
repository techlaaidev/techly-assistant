"""Persistent memory — simple knowledge graph stored as JSON.

No external dependencies. Stores entities, observations, relations.
Auto-loaded across sessions.
"""
import json
from datetime import datetime
from ._common import _reply, DATA_DIR

MEMORY_FILE = DATA_DIR / "memory.json"


def _load() -> dict:
    if not MEMORY_FILE.exists():
        return {"entities": {}, "relations": []}
    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"entities": {}, "relations": []}


def _save(data: dict) -> None:
    MEMORY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register(mcp):
    @mcp.tool()
    def nho_thong_tin(thuc_the: str, noi_dung: str) -> str:
        """Lưu một thông tin về một thực thể (người, vật, sự kiện) vào bộ nhớ dài hạn.

        GỌI TOOL NÀY KHI người dùng nói: "nhớ là tôi thích X", "ghi nhớ rằng Y",
        "đặc điểm của Z là W".
        Ví dụ: "nhớ là tôi thích cà phê đen" → nho_thong_tin("tôi", "thích cà phê đen")

        Args:
            thuc_the: tên thực thể (người, đối tượng, dự án, ...)
            noi_dung: thông tin / observation / fact về thực thể
        """
        data = _load()
        key = thuc_the.lower().strip()
        if key not in data["entities"]:
            data["entities"][key] = {
                "name": thuc_the,
                "observations": [],
                "created_at": datetime.now().isoformat(),
            }
        data["entities"][key]["observations"].append({
            "text": noi_dung,
            "added_at": datetime.now().isoformat(),
        })
        _save(data)
        return f"Đã ghi nhớ về '{thuc_the}': {noi_dung}"

    @mcp.tool()
    def nho_lai(thuc_the: str) -> str:
        """Truy xuất tất cả thông tin đã lưu về một thực thể.

        GỌI TOOL NÀY KHI người dùng hỏi: "tôi đã nói gì về X", "nhớ lại về X",
        "trước đây nói gì về Y".
        """
        data = _load()
        key = thuc_the.lower().strip()
        if key not in data["entities"]:
            return f"Chưa có thông tin nào về '{thuc_the}' trong bộ nhớ."
        ent = data["entities"][key]
        obs = ent.get("observations", [])
        if not obs:
            return f"Chưa có observation nào về '{thuc_the}'."
        lines = [f"- {o['text']}" for o in obs]
        return _reply(f"Về '{thuc_the}' ({len(obs)} ghi nhớ):\n" + "\n".join(lines))

    @mcp.tool()
    def liet_ke_thuc_the() -> str:
        """Liệt kê tất cả thực thể đã được ghi nhớ.

        GỌI TOOL NÀY KHI người dùng hỏi: "đã nhớ những gì", "list memory", "biết những ai".
        """
        data = _load()
        ents = data.get("entities", {})
        if not ents:
            return "Bộ nhớ đang trống."
        lines = [
            f"- {e['name']} ({len(e.get('observations', []))} ghi nhớ)"
            for e in ents.values()
        ]
        return _reply(f"Có {len(ents)} thực thể trong bộ nhớ:\n" + "\n".join(lines))

    @mcp.tool()
    def quen_thuc_the(thuc_the: str) -> str:
        """Xóa hoàn toàn một thực thể khỏi bộ nhớ.

        GỌI TOOL NÀY KHI người dùng nói: "quên X", "xóa thông tin về X".
        """
        data = _load()
        key = thuc_the.lower().strip()
        if key not in data["entities"]:
            return f"Không có '{thuc_the}' trong bộ nhớ."
        del data["entities"][key]
        _save(data)
        return f"Đã quên '{thuc_the}'."
