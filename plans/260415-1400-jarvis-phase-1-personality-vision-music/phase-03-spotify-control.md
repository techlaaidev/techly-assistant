---
title: "Phase 03 — Spotify Music Control"
status: pending
priority: P2
effort: 3h
---

# Phase 03 — Spotify Music Control

## Context Links

- Research: `plans/260415-jarvis-features-research/research/researcher-260415-1244-jarvis-features.md` § Feature 4
- Server registration pattern: `server.py` lines 99-106
- Tool pattern reference: `tools/browser_use_agent.py`
- Shared helpers: `tools/_common.py`
- Env template: `.env.example`
- Home Assistant integration (comparable pattern): `tools/home_assistant.py`

## Overview

**Priority:** P2 — high demo value, requires external setup (Premium + Dev App)  
**Status:** pending  
5 new voice tools for Spotify playback control: play, pause, resume, skip, volume. Single new file `tools/spotify_control.py` + one-time OAuth setup script. Enabled via `ENABLE_SPOTIFY=1`.

## Key Insights (from research)

- `spotipy 2.25.x` is the standard Spotify Python client — 5.5k stars, Feb 2025 last commit
- OAuth PKCE flow for desktop apps: opens browser once → stores token → auto-refreshes
- Spotify Premium required for all playback control APIs (`/me/player/play`, `/me/player/pause`, etc.)
- Free tier: search/browse only — playback endpoints return 403
- Active Spotify Connect device required at call time — desktop app, web player, or device
- `localhost:8888/callback` is the conventional redirect URI for local dev
- Token cache in `data/spotify_token.json` — must be gitignored
- spotipy handles token refresh automatically if `cache_path` provided to `SpotifyOAuth`

## Requirements

### Functional
- `phat_nhac(query: str)` — search + start playback (track, artist, playlist, genre/mood)
- `tam_dung_nhac()` — pause current playback
- `tiep_tuc_nhac()` — resume paused playback
- `chuyen_bai_tiep()` — skip to next track
- `chinh_am_luong(phan_tram: int)` — set volume 0-100
- Clear Vietnamese error if no active Spotify device found
- Clear Vietnamese error if Spotify Premium not active
- First-run OAuth: auto-open browser, complete login, cache token

### Non-functional
- File `tools/spotify_control.py` < 200 lines
- `scripts/spotify-oauth-setup.py` < 80 lines (standalone helper)
- Token cache at `data/spotify_token.json` (never committed)
- spotipy reads `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI` at call-time
- Lazy client init — `_get_client()` called inside each tool, not at module load
- Tool set disabled entirely when `ENABLE_SPOTIFY` unset

## Architecture

```
Voice: "bật nhạc lo-fi đi Techly"
    ↓ Xiaozhi cloud LLM → function call: phat_nhac(query="lo-fi")
    ↓ server.py → tools/spotify_control.py::phat_nhac()
    ↓ _get_client() → SpotifyOAuth(cache_path="data/spotify_token.json")
    ↓ sp.search(q="lo-fi", type="track,playlist", limit=5)
    ↓ sp.start_playback(uris=[best_uri])
    ↓ return _reply("Đang phát: Lo-fi Hip Hop Radio")
    ↓ Xiaozhi TTS → ESP32 speaker
```

### OAuth First-Run Flow

```
User runs: python scripts/spotify-oauth-setup.py
    ↓ SpotifyOAuth opens browser → xiaozhi.me → spotify auth page
    ↓ User logs in + approves scopes
    ↓ Redirect to localhost:8888/callback
    ↓ spotipy captures code → exchanges for token → writes data/spotify_token.json
    ↓ "Setup complete. Token saved." message
    ↓ Server restart → _get_client() reads cached token → auto-refresh on expiry
```

### Data Flow per Tool

| Tool | Spotify API endpoint | Input | Output |
|------|---------------------|-------|--------|
| `phat_nhac` | `search` + `start_playback` | query string | track name + artist |
| `tam_dung_nhac` | `pause_playback` | none | ack string |
| `tiep_tuc_nhac` | `start_playback` (no uri = resume) | none | ack string |
| `chuyen_bai_tiep` | `next_track` | none | ack string |
| `chinh_am_luong` | `volume` | 0-100 int | ack string |

### server.py Integration

```python
if os.getenv("ENABLE_SPOTIFY", "").lower() in ("1", "true", "yes"):
    from tools import spotify_control
    spotify_control.register(mcp)
```

## Related Code Files

### Create
- `tools/spotify_control.py` — 5 tools, `_get_client()`, `register(mcp)` (~180 lines)
- `scripts/spotify-oauth-setup.py` — standalone one-time OAuth helper (~60 lines)

### Modify
- `server.py` — add conditional registration block (3 lines, after ENABLE_SCREEN_VISION block)
- `.env.example` — add Spotify section (5 env vars + comments)
- `requirements.txt` — add `spotipy>=2.25.0`
- `.gitignore` — add `data/spotify_token.json` (verify not already covered by `data/*.json` glob)

### Delete
- None

## Implementation Steps

1. **Prerequisites check** (before coding):
   - Spotify Premium account active
   - Create Spotify Developer App at https://developer.spotify.com/dashboard
     - App name: "Techly Assistant"
     - Redirect URI: `http://localhost:8888/callback`
     - Copy `Client ID` and `Client Secret`
   - Add to `.env`: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI=http://localhost:8888/callback`

2. **Install spotipy**:
   ```
   pip install spotipy>=2.25.0
   ```

3. **Create `scripts/spotify-oauth-setup.py`** — standalone script:
   ```
   Load .env manually (same parser as server.py)
   Import spotipy, SpotifyOAuth
   Define SCOPES = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
   Create SpotifyOAuth(client_id, client_secret, redirect_uri, scope=SCOPES, cache_path="data/spotify_token.json")
   Call sp.get_access_token(as_dict=False) → triggers browser open + callback
   Print "Setup hoàn tất. Token đã lưu tại data/spotify_token.json"
   Print "Restart mcp_pipe.py để dùng Spotify tools."
   ```

4. **Create `tools/spotify_control.py`** with structure:
   ```
   module docstring (requirements, scopes, ENABLE_SPOTIFY, first-run instructions)
   
   imports: os; try/except spotipy → HAS_SPOTIPY flag
   
   SPOTIFY_SCOPES = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
   TOKEN_CACHE = str(BASE_DIR / "data" / "spotify_token.json")  # from _common BASE_DIR
   
   _client_cache = None  # module-level singleton
   
   def _get_client():
       reads SPOTIFY_CLIENT_ID, CLIENT_SECRET, REDIRECT_URI at call-time
       returns spotipy.Spotify(auth_manager=SpotifyOAuth(..., cache_path=TOKEN_CACHE))
       caches in _client_cache for reuse within session
   
   def _handle_spotify_error(e) -> str:
       SpotifyException 403 → "Cần Spotify Premium để điều khiển phát nhạc, thưa ngài."
       SpotifyException 404 → "Không tìm thấy thiết bị Spotify đang hoạt động. Cần mở Spotify app trước."
       SpotifyException 401 → "Token Spotify hết hạn. Chạy lại scripts/spotify-oauth-setup.py"
       else → f"Lỗi Spotify: {str(e)[:200]}"
   
   def register(mcp):
       5 @mcp.tool() decorated functions
   ```

5. **Tool: `phat_nhac(query: str)`**:
   - Search: `sp.search(q=query, type="track,playlist", limit=5)`
   - Prefer track over playlist for specific song queries
   - Pick `items[0]` from tracks; if empty, try playlists
   - `sp.start_playback(uris=[uri])` — starts on active device
   - Return: `_reply(f"Đang phát: {track_name} - {artist_name}")`
   - On SpotifyException: `_handle_spotify_error(e)`

6. **Tools: `tam_dung_nhac()`, `tiep_tuc_nhac()`, `chuyen_bai_tiep()`**:
   - Simple wrappers: `sp.pause_playback()`, `sp.start_playback()`, `sp.next_track()`
   - Return Vietnamese ack strings (no `_reply` prefix needed — not data-fetch tools)
   - Wrap in try/except → `_handle_spotify_error(e)`

7. **Tool: `chinh_am_luong(phan_tram: int)`**:
   - Clamp input: `phan_tram = max(0, min(100, phan_tram))`
   - `sp.volume(phan_tram)`
   - Return: `f"Âm lượng đã chỉnh về {phan_tram}%, thưa ngài."`

8. **Docstring trigger phrases** for `phat_nhac`:
   ```
   GỌI TOOL NÀY KHI người dùng nói:
   - "bật nhạc", "phát nhạc", "mở nhạc", "cho tôi nghe nhạc"
   - "bật [tên bài/nghệ sĩ/thể loại]": "bật lo-fi", "bật Sơn Tùng", "bật jazz"
   - "play [query]", "phát [query]"
   KHÔNG gọi tool này cho: radio, YouTube, tivi
   ```

9. **Modify `server.py`**: add after ENABLE_SCREEN_VISION block:
   ```python
   if os.getenv("ENABLE_SPOTIFY", "").lower() in ("1", "true", "yes"):
       from tools import spotify_control
       spotify_control.register(mcp)
   ```

10. **Update `.env.example`**: add section:
    ```
    # === Spotify Music Control (optional) — voice-controlled playback ===
    # Requires: Spotify Premium + Developer App at https://developer.spotify.com/dashboard
    # First-run setup: python scripts/spotify-oauth-setup.py
    # Token auto-refreshes; cached at data/spotify_token.json (gitignored)
    ENABLE_SPOTIFY=
    SPOTIFY_CLIENT_ID=
    SPOTIFY_CLIENT_SECRET=
    SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
    ```

11. **Update `.gitignore`**: verify or add `data/spotify_token.json`.

12. **Test sequence**:
    - Run `python scripts/spotify-oauth-setup.py` → browser opens → login → token saved
    - Set `ENABLE_SPOTIFY=1` in `.env`; restart `mcp_pipe.py`
    - Open Spotify desktop app (creates active Connect device)
    - Say: "bật nhạc lo-fi" → verify playback starts
    - Say: "tạm dừng nhạc" → verify pause
    - Say: "chỉnh âm lượng 50%" → verify volume change
    - Say: "chuyển bài tiếp theo" → verify skip

## Todo List

- [ ] Create Spotify Developer App + get Client ID/Secret
- [ ] Add `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI` to `.env`
- [ ] Install `spotipy>=2.25.0` in project venv
- [ ] Create `scripts/spotify-oauth-setup.py` (standalone, under 80 lines)
- [ ] Run OAuth setup → verify `data/spotify_token.json` created
- [ ] Create `tools/spotify_control.py` with `register(mcp)`, `_get_client()`, `_handle_spotify_error()`
- [ ] Implement `phat_nhac()` with search + playback + docstring trigger phrases
- [ ] Implement `tam_dung_nhac()`, `tiep_tuc_nhac()`, `chuyen_bai_tiep()`
- [ ] Implement `chinh_am_luong()` with 0-100 clamp
- [ ] Add HAS_SPOTIPY ImportError guard
- [ ] Modify `server.py` — conditional registration block
- [ ] Update `.env.example` — Spotify section
- [ ] Update `requirements.txt` — `spotipy>=2.25.0`
- [ ] Verify `data/spotify_token.json` is gitignored
- [ ] Test: all 5 tools register when `ENABLE_SPOTIFY=1`
- [ ] Test: tools absent from `tools/list` when env var unset
- [ ] Test: `phat_nhac("lo-fi")` starts playback
- [ ] Test: `tam_dung_nhac()` + `tiep_tuc_nhac()` cycle works
- [ ] Test: no-device error returns Vietnamese message (close Spotify app, test)
- [ ] Test: `chinh_am_luong(150)` clamps to 100 without error

## Success Criteria

- `phat_nhac("lo-fi")` starts Spotify playback and returns track name in Vietnamese response
- `tam_dung_nhac()` pauses; `tiep_tuc_nhac()` resumes — confirmed audibly
- `chinh_am_luong(50)` changes volume to 50%
- No active device → returns "Cần mở Spotify app trước" (not a Python traceback)
- `server.py` starts without error when `ENABLE_SPOTIFY` unset
- `data/spotify_token.json` not tracked by git

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| No active Spotify Connect device at query time | High | Medium | `_handle_spotify_error` catches 404 → clear Vietnamese message |
| Free account (not Premium) returns 403 | Medium | High | 403 handler returns explicit Premium requirement message |
| OAuth token refresh fails silently | Low | High | spotipy auto-refreshes via `SpotifyOAuth`; if fails → 401 caught → re-setup message |
| `localhost:8888` port already in use during OAuth setup | Low | Medium | spotipy uses ephemeral server; conflict rare; doc says close other apps |
| `sp.search()` returns empty for obscure VN artists | Medium | Low | Fallback: return "Không tìm thấy '{query}' trên Spotify" gracefully |
| spotipy 2.25 + Python 3.14 compat | Low | Medium | Check PyPI before install; spotipy has no C extensions, pure Python |
| Token cache file permissions on Windows | Low | Low | `data/` dir created by `_common.py` at import; writable by default |
| Developer App "quota extension" needed for production | Low | Low | Hobby use stays in Development Mode (25 users max) — fine for single user |

## Security Considerations

- `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` — sensitive, read at call-time via `os.getenv()`, never hardcoded or logged
- `data/spotify_token.json` — contains OAuth access + refresh tokens; must be gitignored; check `.gitignore` before first commit
- OAuth PKCE flow: tokens scoped to `user-modify-playback-state user-read-playback-state user-read-currently-playing` only — minimal required scopes
- Redirect URI `http://localhost:8888/callback` — local only, not exposed to network
- Never log token values in any print/stderr output

## Next Steps

- After Phase 3: combine with Home Assistant in voice commands ("bật nhạc lo-fi và tắt đèn phòng khách")
- Phase 2 (Spotify) road leads naturally to Phase 2 of Jarvis roadmap: APScheduler + proactive push
- Future: `xem_dang_phat()` tool to show current track info (read-only, no Premium required) — not this phase

## Unresolved Questions

1. Does spotipy 2.25.x support Python 3.14? (No C extensions so likely yes — verify in venv)
2. Spotify Developer App: does Development Mode (25 users) require any approval for single-user hobby use? (Expected: no)
3. `sp.start_playback()` with no `device_id` param — does it default to last active device or throw 404 if ambiguous? (Test empirically during setup)
4. VN-language search queries: does `sp.search(q="nhạc lo-fi thư giãn")` return usable results or should query be transliterated to English? (Test with a few VN phrases)
