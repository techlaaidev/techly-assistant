"""Local filesystem operations within a configured root directory.

For safety, only operates within data/files/ subdirectory.
"""
from ._common import _reply, DATA_DIR

FILES_ROOT = DATA_DIR / "files"
FILES_ROOT.mkdir(parents=True, exist_ok=True)


def _safe_path(name: str):
    """Resolve name within FILES_ROOT, prevent directory traversal."""
    target = (FILES_ROOT / name).resolve()
    if not str(target).startswith(str(FILES_ROOT.resolve())):
        return None
    return target


def register(mcp):
    @mcp.tool()
    def liet_ke_file() -> str:
        """Liệt kê các file trong thư mục files cá nhân.

        GỌI TOOL NÀY KHI người dùng hỏi: "có file gì", "list file", "xem file của tôi".
        """
        files = sorted(FILES_ROOT.glob("*"))
        if not files:
            return "Chưa có file nào trong thư mục cá nhân."
        lines = [f"- {f.name} ({f.stat().st_size} bytes)" for f in files if f.is_file()]
        if not lines:
            return "Chưa có file nào."
        return _reply("Các file hiện có:\n" + "\n".join(lines))

    @mcp.tool()
    def doc_file(ten_file: str) -> str:
        """Đọc nội dung một file text trong thư mục cá nhân.

        GỌI TOOL NÀY KHI người dùng nói: "đọc file X", "nội dung của file Y".

        Args:
            ten_file: tên file (vd "ghi_chu.txt")
        """
        path = _safe_path(ten_file)
        if not path or not path.exists() or not path.is_file():
            return f"Không tìm thấy file '{ten_file}'."
        try:
            content = path.read_text(encoding="utf-8")
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            return _reply(f"Nội dung file '{ten_file}':\n\n{content}")
        except Exception as e:
            return f"Không đọc được file: {str(e)[:100]}"

    @mcp.tool()
    def viet_file(ten_file: str, noi_dung: str) -> str:
        """Tạo / ghi đè một file text trong thư mục cá nhân.

        GỌI TOOL NÀY KHI người dùng nói: "lưu thành file X", "tạo file Y với nội dung Z".

        Args:
            ten_file: tên file
            noi_dung: nội dung text
        """
        path = _safe_path(ten_file)
        if not path:
            return "Tên file không hợp lệ."
        try:
            path.write_text(noi_dung, encoding="utf-8")
            return f"Đã lưu file '{ten_file}' ({len(noi_dung)} ký tự)."
        except Exception as e:
            return f"Không ghi được file: {str(e)[:100]}"

    @mcp.tool()
    def xoa_file(ten_file: str) -> str:
        """Xóa một file trong thư mục cá nhân.

        GỌI TOOL NÀY KHI người dùng nói: "xóa file X".
        """
        path = _safe_path(ten_file)
        if not path or not path.exists():
            return f"Không tìm thấy file '{ten_file}'."
        try:
            path.unlink()
            return f"Đã xóa file '{ten_file}'."
        except Exception as e:
            return f"Không xóa được: {str(e)[:100]}"
