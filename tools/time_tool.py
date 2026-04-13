"""Current time/date in Vietnamese."""
from datetime import datetime
from ._common import _reply


def register(mcp):
    @mcp.tool()
    def lay_thoi_gian_hien_tai() -> str:
        """Trả về ngày giờ hiện tại (giờ, phút, thứ, ngày, tháng, năm) bằng tiếng Việt.

        GỌI TOOL NÀY KHI người dùng hỏi về: giờ, thời gian, ngày mấy, thứ mấy, bây giờ mấy giờ.
        Ví dụ: "mấy giờ rồi", "hôm nay thứ mấy", "ngày bao nhiêu".
        """
        now = datetime.now()
        weekdays = ["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm",
                    "thứ Sáu", "thứ Bảy", "Chủ nhật"]
        weekday = weekdays[now.weekday()]
        return _reply(
            f"Hiện tại là {now.strftime('%H giờ %M phút')}, "
            f"{weekday}, ngày {now.day} tháng {now.month} năm {now.year}."
        )
