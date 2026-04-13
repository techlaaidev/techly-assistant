"""Personal notes tools (file-based)."""
from datetime import datetime
from ._common import _reply, NOTES_FILE


def register(mcp):
    @mcp.tool()
    def ghi_chu(noi_dung: str) -> str:
        """Lưu một ghi chú mới vào file cá nhân (kèm timestamp).

        GỌI TOOL NÀY KHI người dùng nói: "ghi chú", "nhắc tôi", "lưu lại", "ghi lại".
        Ví dụ: "ghi chú mai họp 9h", "lưu lại số điện thoại 0901234567".

        Args:
            noi_dung: Nội dung cần ghi (trích từ lời người dùng)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with NOTES_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {noi_dung}\n")
        return f"Đã ghi chú: {noi_dung}"

    @mcp.tool()
    def doc_ghi_chu() -> str:
        """Đọc lại tất cả ghi chú đã lưu.

        GỌI TOOL NÀY KHI người dùng hỏi: "ghi chú của tôi", "tôi đã ghi gì", "xem note".
        """
        if not NOTES_FILE.exists():
            return _reply("Chưa có ghi chú nào.")
        content = NOTES_FILE.read_text(encoding="utf-8").strip()
        return _reply(content if content else "Chưa có ghi chú nào.")

    @mcp.tool()
    def xoa_ghi_chu() -> str:
        """Xóa toàn bộ ghi chú đã lưu.

        GỌI TOOL NÀY KHI người dùng nói: "xóa hết ghi chú", "xóa note".
        CẨN THẬN: nên xác nhận trước khi gọi.
        """
        if NOTES_FILE.exists():
            NOTES_FILE.unlink()
        return "Đã xóa tất cả ghi chú."
