"""Weather tool using open-meteo.com free API (no key required)."""
import json
import urllib.request
from ._common import _reply

_VN_CITY_COORDS = {
    "hà nội": (21.0285, 105.8542),
    "hanoi": (21.0285, 105.8542),
    "hồ chí minh": (10.7626, 106.6602),
    "tp hcm": (10.7626, 106.6602),
    "sài gòn": (10.7626, 106.6602),
    "đà nẵng": (16.0544, 108.2022),
    "cần thơ": (10.0452, 105.7469),
    "hải phòng": (20.8449, 106.6881),
    "huế": (16.4637, 107.5909),
    "nha trang": (12.2388, 109.1967),
    "vũng tàu": (10.3460, 107.0843),
    "biên hòa": (10.9574, 106.8426),
}

_WEATHER_DESC = {
    0: "trời nắng", 1: "trời quang", 2: "có mây rải rác", 3: "nhiều mây",
    45: "sương mù", 48: "sương mù đóng băng",
    51: "mưa phùn nhẹ", 53: "mưa phùn", 55: "mưa phùn nặng hạt",
    61: "mưa nhẹ", 63: "mưa vừa", 65: "mưa to",
    71: "tuyết nhẹ", 73: "tuyết vừa", 75: "tuyết to",
    80: "mưa rào nhẹ", 81: "mưa rào vừa", 82: "mưa rào to",
    95: "giông bão", 96: "giông có mưa đá nhẹ", 99: "giông có mưa đá to",
}


def register(mcp):
    @mcp.tool()
    def lay_thoi_tiet(thanh_pho: str = "Hà Nội") -> str:
        """Trả về thời tiết hiện tại của một thành phố Việt Nam (nhiệt độ, độ ẩm, gió).

        GỌI TOOL NÀY KHI người dùng hỏi về: thời tiết, nắng mưa, nóng lạnh, gió.
        Ví dụ: "thời tiết Hà Nội", "Sài Gòn nóng không", "Đà Nẵng mưa không".
        Hỗ trợ: Hà Nội, TP HCM, Đà Nẵng, Cần Thơ, Hải Phòng, Huế, Nha Trang, Vũng Tàu, Biên Hòa.

        Args:
            thanh_pho: Tên thành phố (mặc định "Hà Nội")
        """
        key = thanh_pho.lower().strip()
        if key not in _VN_CITY_COORDS:
            avail = ", ".join(sorted(set(_VN_CITY_COORDS.keys())))
            return f"Không có dữ liệu cho '{thanh_pho}'. Các thành phố hỗ trợ: {avail}"

        lat, lon = _VN_CITY_COORDS[key]
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            f"&timezone=Asia/Bangkok"
        )
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return f"Lỗi kết nối dịch vụ thời tiết: {e}"

        current = data.get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        code = current.get("weather_code", 0)
        desc = _WEATHER_DESC.get(code, "thời tiết không xác định")

        return _reply(
            f"Thời tiết {thanh_pho}: {desc}, "
            f"nhiệt độ {temp}°C, độ ẩm {humidity}%, gió {wind} km/h."
        )
