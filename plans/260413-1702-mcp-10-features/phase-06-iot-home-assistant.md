---
phase: 6
title: IoT smart home — Home Assistant integration
status: pending
effort: 2h
priority: medium
blockedBy_external: [Home Assistant instance + Long-Lived Access Token]
---

# Phase 6: Home Assistant IoT

## Context
Smart home control là killer use case của voice assistant. Integrate với Home Assistant (đã là standard). User cần:
1. HA instance chạy (cloud/local)
2. Long-Lived Access Token từ HA profile

## Prerequisites (user side)

1. HA instance: http://homeassistant.local:8123 hoặc IP
2. Vào Profile → Long-Lived Access Tokens → Create Token
3. Lưu token + base URL vào env vars:
   ```
   HA_URL=http://192.168.1.50:8123
   HA_TOKEN=eyJxxxxx.xxxxx.xxxxx
   ```

## Features

### 6.1 Control entities
**Tool:** `dieu_khien_thiet_bi(entity: str, hanh_dong: str)`

Ví dụ:
- "bật đèn phòng khách" → `dieu_khien_thiet_bi("light.phong_khach", "turn_on")`
- "tắt điều hoà" → `dieu_khien_thiet_bi("climate.phong_ngu", "turn_off")`

### 6.2 Query status
**Tool:** `trang_thai_thiet_bi(entity: str)`

### 6.3 Set temperature / brightness
**Tool:** `dat_nhiet_do(entity: str, nhiet_do: int)`
**Tool:** `dat_do_sang(entity: str, phan_tram: int)`

### 6.4 List all entities
**Tool:** `liet_ke_thiet_bi()` — từ HA `/api/states`

## HA REST API reference

```
GET  /api/states                    → list all entities
GET  /api/states/{entity_id}        → entity state
POST /api/services/{domain}/{service} → call service
     body: {"entity_id": "light.x"}
```

Auth: `Authorization: Bearer {HA_TOKEN}`

## Implementation

```python
import os, json, urllib.request
from ._common import _reply

HA_URL = os.getenv("HA_URL", "").rstrip("/")
HA_TOKEN = os.getenv("HA_TOKEN", "")

def _ha_request(method: str, path: str, body: dict = None) -> dict:
    if not HA_URL or not HA_TOKEN:
        raise RuntimeError("HA_URL or HA_TOKEN not set in environment")
    req = urllib.request.Request(
        f"{HA_URL}/api{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    if body:
        req.data = json.dumps(body).encode("utf-8")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def register(mcp):
    @mcp.tool()
    def dieu_khien_thiet_bi(entity: str, hanh_dong: str) -> str:
        """Bật/tắt thiết bị thông minh trong nhà qua Home Assistant.

        GỌI TOOL NÀY KHI người dùng ra lệnh: bật/tắt đèn, quạt, điều hoà, TV.
        Ví dụ: "bật đèn phòng khách", "tắt quạt", "mở điều hoà".
        entity: dạng "light.phong_khach", "switch.quat", "climate.phong_ngu"
        hanh_dong: "turn_on" hoặc "turn_off"
        """
        domain = entity.split(".")[0]
        service = hanh_dong  # turn_on | turn_off
        try:
            _ha_request("POST", f"/services/{domain}/{service}",
                       {"entity_id": entity})
            return f"Đã {hanh_dong.replace('turn_on','bật').replace('turn_off','tắt')} {entity}."
        except Exception as e:
            return f"Không điều khiển được {entity}: {str(e)[:100]}"

    # ... trang_thai_thiet_bi, dat_nhiet_do, dat_do_sang, liet_ke_thiet_bi
```

## Files to create

- `tools/home_assistant.py`
- `.env.example` (template cho HA_URL, HA_TOKEN)

## Todo

- [ ] User setup: HA running + long-lived token
- [ ] Load env vars from `.env` file (use `python-dotenv` hoặc os.environ)
- [ ] Create `tools/home_assistant.py` với 5 tools
- [ ] Error handling khi HA offline
- [ ] Register in `server.py`
- [ ] Voice test: "bật đèn phòng khách", "trạng thái điều hoà"

## Success criteria

- Tools hoạt động với HA instance thực
- Error khi HA offline/token sai → message rõ ràng, không crash server
- Entity mapping từ VN name → HA entity_id (LLM tự làm qua context, hoặc có tool `tim_entity`)

## Risks

- User chưa có HA → skip phase này hoàn toàn
- Entity naming phức tạp (dấu Việt vs english) → LLM tự map qua system prompt + entity list
- Network local only → MCP server phải chung LAN với HA

## Non-goals

- Không support HA automations / scripts qua tool này
- Không support multi-user / multi-HA
