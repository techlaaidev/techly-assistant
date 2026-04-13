"""Currency exchange, gold price, VN stocks, VN-Index."""
import json
import re
import urllib.request
from ._common import _reply


def _http_get(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def register(mcp):
    @mcp.tool()
    def lay_ty_gia(tien_te: str = "USD") -> str:
        """Trả về tỷ giá ngoại tệ so với đồng Việt Nam (VND).

        GỌI TOOL NÀY KHI người dùng hỏi: "tỷ giá đô", "1 USD bao nhiêu tiền Việt",
        "giá đô hôm nay", "tỷ giá euro".
        Hỗ trợ: USD, EUR, JPY, KRW, CNY, GBP, AUD, SGD, THB.
        """
        code = tien_te.upper().strip()
        url = f"https://api.exchangerate.host/latest?base={code}&symbols=VND"
        try:
            data = json.loads(_http_get(url))
            rate = data.get("rates", {}).get("VND")
            if not rate:
                url2 = f"https://open.er-api.com/v6/latest/{code}"
                data2 = json.loads(_http_get(url2))
                rate = data2.get("rates", {}).get("VND")
            if not rate:
                return f"Không lấy được tỷ giá cho {code}."
            return _reply(f"1 {code} = {rate:,.0f} đồng Việt Nam.".replace(",", "."))
        except Exception as e:
            return f"Lỗi tỷ giá: {str(e)[:100]}"

    @mcp.tool()
    def gia_vang_sjc() -> str:
        """Trả về giá vàng SJC hiện tại (mua vào và bán ra).

        GỌI TOOL NÀY KHI người dùng hỏi: "giá vàng", "vàng SJC bao nhiêu", "giá vàng hôm nay".
        """
        try:
            html = _http_get("https://sjc.com.vn/giavang/textContent.php")
            # Parse first row with numbers > 1 million
            prices = re.findall(r"(\d[\d,\.]{6,})", html)
            nums = []
            for p in prices:
                n = int(p.replace(",", "").replace(".", ""))
                if 10_000_000 < n < 200_000_000:
                    nums.append(n)
            if len(nums) < 2:
                return "Không lấy được giá vàng SJC. Thử lại sau."
            mua, ban = nums[0], nums[1]
            return _reply(
                f"Vàng SJC: mua vào {mua:,.0f} đồng/lượng, "
                f"bán ra {ban:,.0f} đồng/lượng.".replace(",", ".")
            )
        except Exception as e:
            return f"Lỗi lấy giá vàng: {str(e)[:100]}"

    @mcp.tool()
    def gia_co_phieu(ma_ck: str) -> str:
        """Trả về giá cổ phiếu VN (mã 3 ký tự như VCB, FPT, VIC, HPG...).

        GỌI TOOL NÀY KHI người dùng hỏi: "giá VCB", "chứng khoán FPT", "cổ phiếu HPG".
        Args:
            ma_ck: mã chứng khoán (viết hoa, 3 ký tự)
        """
        ma = ma_ck.upper().replace(" ", "").strip()
        url = f"https://api-finfo.vndirect.com.vn/v4/stock_prices?q=code:{ma}&sort=date:desc&size=1"
        try:
            data = json.loads(_http_get(url))
            items = data.get("data", [])
            if not items:
                return f"Không tìm thấy mã {ma}."
            item = items[0]
            close = item.get("close", 0)
            pct = item.get("percentChange", 0)
            date = item.get("date", "")
            direction = "tăng" if pct >= 0 else "giảm"
            return _reply(
                f"Cổ phiếu {ma} ngày {date}: giá {close:,.0f} đồng, "
                f"{direction} {abs(pct):.2f}%.".replace(",", ".")
            )
        except Exception as e:
            return f"Không lấy được giá {ma}: {str(e)[:100]}"

    @mcp.tool()
    def vnindex_hien_tai() -> str:
        """Trả về chỉ số VN-Index hiện tại.

        GỌI TOOL NÀY KHI người dùng hỏi: "VN-Index", "chỉ số chứng khoán", "thị trường hôm nay".
        """
        url = "https://api-finfo.vndirect.com.vn/v4/stock_prices?q=code:VNINDEX&sort=date:desc&size=1"
        try:
            data = json.loads(_http_get(url))
            items = data.get("data", [])
            if not items:
                return "Không lấy được VN-Index lúc này."
            item = items[0]
            close = item.get("close", 0)
            pct = item.get("percentChange", 0)
            direction = "tăng" if pct >= 0 else "giảm"
            return _reply(
                f"VN-Index: {close:.2f} điểm, {direction} {abs(pct):.2f}% so với phiên trước."
            )
        except Exception as e:
            return f"Lỗi VN-Index: {str(e)[:100]}"
