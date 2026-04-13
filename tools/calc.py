"""Safe calculator for simple arithmetic expressions."""
import re


def register(mcp):
    @mcp.tool()
    def tinh_toan(bieu_thuc: str) -> str:
        """Tính toán một biểu thức số học đơn giản (+, -, *, /, ngoặc).

        GỌI TOOL NÀY KHI người dùng yêu cầu tính toán số học cụ thể.
        Ví dụ: "100 chia 4" → tinh_toan("100/4"). "2 cộng 3 nhân 4" → tinh_toan("2+3*4").
        CHỈ chấp nhận: số, +, -, *, /, dấu ngoặc.

        Args:
            bieu_thuc: Biểu thức toán học dạng ký hiệu (ví dụ "2+3*4")
        """
        if not re.fullmatch(r"[\d\s+\-*/().]+", bieu_thuc):
            return "Biểu thức chỉ được chứa số và các phép toán +, -, *, /, ()."
        try:
            result = eval(bieu_thuc, {"__builtins__": {}}, {})
            return f"{bieu_thuc} = {result}"
        except Exception as e:
            return f"Lỗi tính toán: {e}"
