"""Company data tools (reads from company_data.md)."""
from ._common import _reply, _read_company_section


def register(mcp):
    @mcp.tool()
    def lay_doanh_thu() -> str:
        """Trả về doanh thu công ty theo từng tháng (số liệu triệu VND).

        GỌI TOOL NÀY KHI người dùng hỏi về: doanh thu, doanh số, tiền thu, lợi nhuận, số liệu bán hàng tháng nào đó.
        Ví dụ câu hỏi: "doanh thu tháng 3", "công ty lời bao nhiêu", "doanh số năm nay".
        """
        return _reply(_read_company_section("Doanh thu"))

    @mcp.tool()
    def lay_don_hang() -> str:
        """Trả về tình trạng đơn hàng hôm nay (tổng đơn, đã giao, đang xử lý).

        GỌI TOOL NÀY KHI người dùng hỏi về: đơn hàng hôm nay, số đơn, đã giao chưa, đang xử lý.
        Ví dụ: "hôm nay có bao nhiêu đơn", "đơn hàng thế nào".
        """
        return _reply(_read_company_section("Đơn hàng hôm nay"))

    @mcp.tool()
    def lay_thong_tin_cong_ty() -> str:
        """Trả về thông tin chung công ty Techla AI: tên, lĩnh vực, địa chỉ, hotline, website.

        GỌI TOOL NÀY KHI người dùng hỏi về: công ty, địa chỉ, hotline, website, bao nhiêu nhân viên.
        Ví dụ: "công ty mình ở đâu", "số hotline", "website công ty".
        """
        return _reply(_read_company_section("Thông tin công ty"))

    @mcp.tool()
    def lay_khach_hang_vip() -> str:
        """Trả về danh sách khách hàng VIP (tên, số điện thoại, tổng chi tiêu).

        GỌI TOOL NÀY KHI người dùng hỏi về: khách hàng VIP, khách chi tiêu nhiều nhất, top khách.
        """
        return _reply(_read_company_section("Khách hàng VIP"))

    @mcp.tool()
    def lay_san_pham_ban_chay() -> str:
        """Trả về danh sách sản phẩm bán chạy nhất công ty.

        GỌI TOOL NÀY KHI người dùng hỏi về: sản phẩm bán chạy, mặt hàng hot, bestseller.
        """
        return _reply(_read_company_section("Sản phẩm bán chạy"))

    @mcp.tool()
    def lay_lich_hop() -> str:
        """Trả về lịch họp công ty trong tuần này.

        GỌI TOOL NÀY KHI người dùng hỏi về: lịch họp, meeting công ty, cuộc họp tuần này.
        """
        return _reply(_read_company_section("Lịch họp tuần này"))
