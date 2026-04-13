---
phase: 7
title: Google Calendar integration
status: pending
effort: 3h
priority: low
blockedBy_external: [Google Cloud project + OAuth credentials]
---

# Phase 7: Google Calendar

## Context
Integration phức tạp nhất vì Google OAuth. Ưu tiên thấp — chỉ làm khi user thực sự cần.

## Prerequisites (user side)

1. Google Cloud project: https://console.cloud.google.com/
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json`
5. First run: browser opens → user authorizes → token saved to `token.json`

## Features

### 7.1 List today's events
**Tool:** `xem_lich_hom_nay()` → list events 24h upcoming

### 7.2 List events in range
**Tool:** `xem_lich_trong_tuan()` → events next 7 days

### 7.3 Add event
**Tool:** `them_su_kien(tieu_de: str, thoi_gian: str, thoi_luong_phut: int = 30)`

Ví dụ: "thêm meeting với sếp 3h chiều mai trong 1 tiếng"

## Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

## Implementation sketch

```python
import os
from datetime import datetime, timedelta
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import dateparser
from ._common import _reply, BASE_DIR

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

def _get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def register(mcp):
    @mcp.tool()
    def xem_lich_hom_nay() -> str:
        """Xem lịch sự kiện Google Calendar hôm nay.

        GỌI TOOL NÀY KHI người dùng hỏi: "lịch hôm nay", "có cuộc hẹn nào hôm nay", "meeting hôm nay".
        """
        try:
            service = _get_service()
            now = datetime.utcnow().isoformat() + 'Z'
            tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary', timeMin=now, timeMax=tomorrow,
                singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                return _reply("Hôm nay không có sự kiện nào trên lịch.")
            lines = []
            for e in events:
                start = e['start'].get('dateTime', e['start'].get('date', ''))
                summary = e.get('summary', '(không tiêu đề)')
                lines.append(f"- {start[11:16]}: {summary}")
            return _reply("Lịch hôm nay:\n" + "\n".join(lines))
        except Exception as e:
            return f"Không truy cập được Google Calendar: {str(e)[:150]}"

    # ... them_su_kien, xem_lich_trong_tuan
```

## First run UX issue

- `InstalledAppFlow.run_local_server()` mở browser → user authorize → redirect về localhost
- Vấn đề: server.py chạy như stdio subprocess của mcp_pipe.py → không có foreground terminal
- **Workaround**: user chạy `python server.py --auth` một lần trước, manual authorize, token saved → sau đó stdio mode dùng token.json

```python
if __name__ == "__main__":
    if "--auth" in sys.argv:
        _get_service()  # triggers OAuth flow
        print("✅ Authorized. Now run via mcp_pipe.py")
        sys.exit(0)
    mcp.run(transport="stdio")
```

## Files to create

- `tools/calendar_gcal.py`
- `credentials.json` (user provides)
- `token.json` (auto-generated on first auth)
- Update `.gitignore` → exclude `credentials.json`, `token.json`

## Todo

- [ ] User: setup Google Cloud project + download credentials.json
- [ ] `pip install google-auth google-auth-oauthlib google-api-python-client`
- [ ] Create `tools/calendar_gcal.py` với 3 tools
- [ ] Add `--auth` mode to `server.py` entry
- [ ] Document auth flow trong README
- [ ] Register (conditionally) in `server.py` — skip nếu credentials.json không tồn tại
- [ ] Voice test: "lịch hôm nay", "thêm meeting 4h chiều mai"

## Success criteria

- First run: user run `python server.py --auth`, browser opens, authorize
- Subsequent runs: token.json refreshes automatically
- Tools callable via voice sau khi authorized
- Graceful error nếu token expired + không refresh được

## Risks

- OAuth flow phức tạp → nhiều user sẽ skip phase này
- Credentials leak nếu commit nhầm → `.gitignore` strict
- Google rate limits → voice use case khó hit, OK
- Token refresh fail → user phải re-auth manual

## Alternative nếu không dùng Google

- **CalDAV**: Baikal, Nextcloud self-host → no OAuth
- **iCal file**: read-only, user tự tạo .ics
- **Local JSON**: simpler than Google, mất sync

Ưu tiên Google vì integration native, data đã có sẵn trong lịch personal của user.
