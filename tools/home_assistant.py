"""Home Assistant IoT integration via REST API.

Requires env vars:
    HA_URL      e.g. http://192.168.1.50:8123
    HA_TOKEN    long-lived access token from HA profile
"""
import json
import os
import urllib.request
from ._common import _reply

HA_URL = os.getenv("HA_URL", "").rstrip("/")
HA_TOKEN = os.getenv("HA_TOKEN", "")


def _ha_request(method: str, path: str, body: dict | None = None) -> dict | list:
    if not HA_URL or not HA_TOKEN:
        raise RuntimeError("HA_URL hoặc HA_TOKEN chưa được cấu hình trong environment.")
    req = urllib.request.Request(
        f"{HA_URL}/api{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _vn_action(action: str) -> str:
    return {"turn_on": "bật", "turn_off": "tắt", "toggle": "chuyển trạng thái"}.get(action, action)


def register(mcp):
    @mcp.tool()
    def dieu_khien_thiet_bi(entity_id: str, hanh_dong: str = "turn_on") -> str:
        """Bật/tắt thiết bị thông minh qua Home Assistant.

        GỌI TOOL NÀY KHI người dùng ra lệnh: "bật/tắt đèn/quạt/điều hoà/TV".
        Ví dụ: "bật đèn phòng khách" → dieu_khien_thiet_bi("light.phong_khach", "turn_on")
        Ví dụ: "tắt quạt" → dieu_khien_thiet_bi("switch.quat", "turn_off")

        Args:
            entity_id: dạng "light.ten_phong", "switch.ten_thiet_bi", "climate.ten_phong"
            hanh_dong: "turn_on" | "turn_off" | "toggle"
        """
        try:
            domain = entity_id.split(".")[0]
            _ha_request("POST", f"/services/{domain}/{hanh_dong}",
                        {"entity_id": entity_id})
            return f"Đã {_vn_action(hanh_dong)} {entity_id}."
        except Exception as e:
            return f"Không điều khiển được {entity_id}: {str(e)[:150]}"

    @mcp.tool()
    def trang_thai_thiet_bi(entity_id: str) -> str:
        """Xem trạng thái hiện tại của một thiết bị (on/off, nhiệt độ, ...).

        GỌI TOOL NÀY KHI người dùng hỏi: "đèn X đang bật hay tắt", "nhiệt độ điều hoà".
        Args:
            entity_id: id thiết bị (vd "light.phong_khach")
        """
        try:
            data = _ha_request("GET", f"/states/{entity_id}")
            state = data.get("state", "unknown")
            attrs = data.get("attributes", {})
            friendly = attrs.get("friendly_name", entity_id)
            extra = []
            if "temperature" in attrs:
                extra.append(f"nhiệt độ {attrs['temperature']}°C")
            if "brightness" in attrs:
                extra.append(f"độ sáng {attrs['brightness']}")
            extra_str = f" ({', '.join(extra)})" if extra else ""
            return _reply(f"{friendly}: {state}{extra_str}")
        except Exception as e:
            return f"Không đọc được trạng thái {entity_id}: {str(e)[:150]}"

    @mcp.tool()
    def dat_nhiet_do(entity_id: str, nhiet_do: int) -> str:
        """Đặt nhiệt độ cho điều hoà / máy lạnh.

        GỌI TOOL NÀY KHI người dùng nói: "điều hoà X độ", "bật lạnh 25".
        Ví dụ: "điều hoà phòng ngủ 25 độ" → dat_nhiet_do("climate.phong_ngu", 25)

        Args:
            entity_id: climate entity (vd "climate.phong_ngu")
            nhiet_do: nhiệt độ °C (16-30)
        """
        if not 16 <= nhiet_do <= 30:
            return "Nhiệt độ phải trong khoảng 16-30°C."
        try:
            _ha_request("POST", "/services/climate/set_temperature",
                        {"entity_id": entity_id, "temperature": nhiet_do})
            return f"Đã đặt {entity_id} về {nhiet_do}°C."
        except Exception as e:
            return f"Không đặt được nhiệt độ: {str(e)[:150]}"

    @mcp.tool()
    def dat_do_sang(entity_id: str, phan_tram: int) -> str:
        """Đặt độ sáng đèn (0-100%).

        GỌI TOOL NÀY KHI người dùng nói: "đèn X sáng Y phần trăm", "giảm đèn còn 50".
        Args:
            entity_id: light entity
            phan_tram: độ sáng 0-100
        """
        if not 0 <= phan_tram <= 100:
            return "Độ sáng phải trong khoảng 0-100%."
        try:
            brightness = int(phan_tram * 2.55)  # 0-255
            _ha_request("POST", "/services/light/turn_on",
                        {"entity_id": entity_id, "brightness": brightness})
            return f"Đã đặt {entity_id} về độ sáng {phan_tram}%."
        except Exception as e:
            return f"Không đặt được độ sáng: {str(e)[:150]}"

    @mcp.tool()
    def liet_ke_thiet_bi() -> str:
        """Liệt kê tất cả thiết bị smart home có sẵn trong Home Assistant.

        GỌI TOOL NÀY KHI người dùng hỏi: "có thiết bị gì", "list thiết bị", "nhà có bao nhiêu đèn".
        """
        try:
            states = _ha_request("GET", "/states")
            if not isinstance(states, list):
                return "Không đọc được danh sách thiết bị."
            # Filter common domains
            keep = ("light", "switch", "climate", "fan", "media_player")
            items = []
            for s in states:
                eid = s.get("entity_id", "")
                if eid.startswith(keep):
                    name = s.get("attributes", {}).get("friendly_name", eid)
                    state = s.get("state", "unknown")
                    items.append(f"- {eid} ({name}): {state}")
            if not items:
                return "Chưa có thiết bị nào."
            return _reply("\n".join(items[:30]))
        except Exception as e:
            return f"Lỗi Home Assistant: {str(e)[:150]}"
