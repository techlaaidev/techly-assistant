---
title: "Phase 02 — Screen Vision"
status: pending
priority: P1
effort: 2-3h
---

# Phase 02 — Screen Vision

## Context Links

- Research: `plans/260415-jarvis-features-research/research/researcher-260415-1244-jarvis-features.md` § Feature 3
- Server registration pattern: `server.py` lines 99-106 (ENABLE_* conditional block)
- Tool pattern reference: `tools/browser_use_agent.py` (register function, try/except, `_reply`)
- Shared helpers: `tools/_common.py`
- Env template: `.env.example`

## Overview

**Priority:** P1 — showstopper demo feature  
**Status:** pending  
New tool `nhin_man_hinh(cau_hoi)` captures primary monitor screenshot via `mss`, resizes via Pillow, encodes base64 JPEG, sends to GPT-4o Vision, returns Vietnamese description. Single new file under 200 lines.

## Key Insights (from research)

- `mss` is pure Python, Windows-native, no DLL/admin required — preferred over `pyautogui.screenshot()`
- `monitors[1]` = primary monitor; `monitors[0]` = virtual combined (all screens)
- Pillow resize to 1280×720 max before encoding keeps payload ~100-200KB → cost ~$0.005/call
- OpenAI SDK already in stack (used by `pc_control.py` for `click_thong_minh`)
- Latency 350-700ms acceptable for voice assistant use case
- Privacy risk: all open windows captured — must document in docstring

## Requirements

### Functional
- `nhin_man_hinh(cau_hoi: str) -> str` — captures screen, asks GPT-4o, returns answer in Vietnamese
- Default question if empty: "Màn hình đang hiển thị gì?"
- Response capped at 400 tokens (voice-friendly length)
- Vietnamese error messages for all failure modes
- Enabled only when `ENABLE_SCREEN_VISION=1`

### Non-functional
- File < 200 lines
- No new top-level imports in `server.py` (conditional block only)
- `OPENAI_API_KEY` reused — no new credential type
- `mss` + `Pillow` added to `requirements.txt`
- Tool disabled gracefully if `mss` or `Pillow` not installed (ImportError guard)

## Architecture

```
Voice: "nhìn màn hình, đây là ứng dụng gì?"
    ↓ Xiaozhi cloud LLM → function call: nhin_man_hinh(cau_hoi="đây là ứng dụng gì?")
    ↓ server.py → tools/screen_vision.py::nhin_man_hinh()
    ↓ mss.grab(monitors[1]) → PIL.Image → thumbnail(1280,720) → JPEG base64
    ↓ OpenAI(model="gpt-4o").chat.completions.create(image + question)
    ↓ response.choices[0].message.content (Vietnamese)
    ↓ _reply(answer) → Xiaozhi TTS → ESP32 speaker
```

### Data Flow

| Step | Input | Transform | Output |
|------|-------|-----------|--------|
| Capture | monitor index | `mss.grab()` | raw RGBA bytes |
| Convert | raw bytes | `Image.frombytes("RGB", size, rgb)` | PIL Image |
| Resize | PIL Image (full res) | `.thumbnail((1280, 720))` | PIL Image ≤1280×720 |
| Encode | PIL Image | `buf.save(JPEG, quality=75)` → `base64.b64encode` | base64 string ~150KB |
| API call | base64 + question | `openai.chat.completions.create` | JSON response |
| Extract | JSON response | `.choices[0].message.content` | answer string |
| Return | answer string | `_reply(answer[:1200])` | MCP tool response |

### server.py Integration

```python
# After existing ENABLE_BROWSER_USE_AGENT block:
if os.getenv("ENABLE_SCREEN_VISION", "").lower() in ("1", "true", "yes"):
    from tools import screen_vision
    screen_vision.register(mcp)
```

Note: import must be inside the `if` block (not top-level) to avoid ImportError when `mss`/`Pillow` absent.

## Related Code Files

### Create
- `tools/screen_vision.py` — new tool module (~120 lines)

### Modify
- `server.py` — add conditional registration block (3 lines)
- `.env.example` — add `ENABLE_SCREEN_VISION` and comment block
- `requirements.txt` — add `mss>=9.0` and `Pillow>=10.3`

### Delete
- None

## Implementation Steps

1. **Install + verify deps** (dev only, not in plan scope):
   ```
   pip install mss Pillow
   ```
   Verify: `python -c "import mss; import PIL; print('ok')"` — must pass before coding.

2. **Create `tools/screen_vision.py`** with structure:
   ```
   module docstring (privacy warning, requirements, env var)
   imports: os, io, base64; try/except mss, PIL, openai → HAS_DEPS flag
   _get_openai_client() — reads OPENAI_API_KEY at call-time (not module load)
   _capture_screen() -> bytes — mss grab monitors[1], PIL resize, JPEG encode
   register(mcp):
       @mcp.tool()
       def nhin_man_hinh(cau_hoi: str = "") -> str:
           docstring with GỌI TOOL NÀY KHI + trigger phrases
           guard: HAS_DEPS check
           guard: OPENAI_API_KEY check
           cau_hoi default fill
           try: capture → encode → api call → extract → _reply(truncate)
           except ImportError: Vietnamese install message
           except openai.AuthenticationError: key invalid message
           except Exception as e: generic Vietnamese error + str(e)[:200]
   ```

3. **Docstring trigger phrases** (critical for cloud LLM routing):
   ```
   GỌI TOOL NÀY KHI người dùng nói:
   - "nhìn màn hình", "xem màn hình", "đọc màn hình"
   - "màn hình đang hiện gì", "đây là gì trên màn hình"
   - "chụp màn hình và phân tích", "screen có gì"
   - "ứng dụng nào đang mở", "tôi đang xem gì"
   ```

4. **`_capture_screen()` implementation notes**:
   - Use `sct.monitors[1]` for primary screen (index 0 is virtual combined)
   - `Image.frombytes("RGB", (img.width, img.height), img.rgb)` — note `.rgb` not `.raw`
   - `.thumbnail((1280, 720))` mutates in place, preserves aspect ratio
   - Save to `io.BytesIO()`, format `"JPEG"`, quality `75`
   - Return `buf.getvalue()` bytes

5. **GPT-4o Vision API call structure**:
   ```python
   messages=[{
       "role": "user",
       "content": [
           {"type": "image_url", "image_url": {
               "url": f"data:image/jpeg;base64,{b64_str}",
               "detail": "low"   # "low" = faster + cheaper, sufficient for screen reading
           }},
           {"type": "text", "text": f"{cau_hoi}\nTrả lời bằng tiếng Việt."}
       ]
   }]
   max_tokens=400
   ```
   Use `detail: "low"` — reduces cost to ~$0.003/call vs $0.005 for "auto".

6. **Modify `server.py`**: add import + register block after `ENABLE_BROWSER_USE_AGENT` block:
   ```python
   if os.getenv("ENABLE_SCREEN_VISION", "").lower() in ("1", "true", "yes"):
       from tools import screen_vision
       screen_vision.register(mcp)
   ```

7. **Update `.env.example`**: add section after `OPENAI_VISION_MODEL` line:
   ```
   # === Screen Vision (optional) — GPT-4o sees your screen on demand ===
   # Requires: pip install mss Pillow
   # Cost: ~$0.003/call with detail=low. Uses OPENAI_API_KEY above.
   # WARNING: captures entire primary monitor including sensitive content.
   ENABLE_SCREEN_VISION=
   ```

8. **Update `requirements.txt`**: add `mss>=9.0` and `Pillow>=10.3` with comments.

9. **Manual test sequence**:
   - Set `ENABLE_SCREEN_VISION=1` in `.env`
   - Open a recognizable app (e.g., Notepad with "Hello Jarvis" text)
   - Restart `mcp_pipe.py`
   - Say: "nhìn màn hình, đọc nội dung cho tôi"
   - Expected: tool fires, returns text content of Notepad in Vietnamese

## Todo List

- [ ] Verify `mss` + `Pillow` installable in project venv (`pip install mss Pillow`)
- [ ] Create `tools/screen_vision.py` with `register(mcp)` function
- [ ] Implement `_capture_screen()` — mss grab → PIL resize → JPEG base64
- [ ] Implement `nhin_man_hinh()` with full docstring + trigger phrases
- [ ] Add ImportError guard (HAS_DEPS pattern from `browser_use_agent.py`)
- [ ] Add OPENAI_API_KEY guard at call-time (not module load — see `pc_control.py` pattern)
- [ ] Add Vietnamese error messages for all failure modes
- [ ] Modify `server.py` — conditional registration block (inside `if`, not top-level import)
- [ ] Update `.env.example` — `ENABLE_SCREEN_VISION` section
- [ ] Update `requirements.txt` — `mss>=9.0`, `Pillow>=10.3`
- [ ] Test: tool registers when `ENABLE_SCREEN_VISION=1`
- [ ] Test: tool absent from `tools/list` when env var unset
- [ ] Test: captures primary monitor and returns Vietnamese description
- [ ] Test: graceful error when `OPENAI_API_KEY` missing

## Success Criteria

- `nhin_man_hinh("đây là gì?")` returns Vietnamese description of screen content within 2s
- Tool appears in `tools/list` only when `ENABLE_SCREEN_VISION=1`
- `server.py` starts without error when `ENABLE_SCREEN_VISION` unset (mss/Pillow not required)
- File `tools/screen_vision.py` stays under 200 lines

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `mss` returns black screenshot on some Windows configs | Low | High | Test on target machine; fallback to `pyautogui.screenshot()` if needed |
| `monitors[1]` index error on single-monitor setup | Low | Medium | Wrap in try/except; fallback to `monitors[0]` if index out of range |
| OpenAI API rate limit during rapid voice queries | Low | Low | 400 max_tokens + detail=low keeps calls fast; add 1s debounce if needed |
| PIL `frombytes` error on non-RGB mss output | Low | Medium | Use `Image.frombytes("RGB", ..., img.rgb)` — `.rgb` strips alpha |
| Python 3.14 + Pillow compat | Low | Medium | Pillow>=10.3 supports 3.12+; verify 3.14 in venv before merge |
| Cost overrun if tool called in tight loop | Low | Low | max_tokens=400 + detail=low caps cost; no auto-polling in implementation |

## Security Considerations

- Screen capture includes ALL open windows — passwords, private docs, etc. Document clearly in docstring
- `OPENAI_API_KEY` read at call-time via `os.getenv()` — never hardcoded, never logged
- Base64 image sent to OpenAI API over HTTPS — same trust boundary as existing `click_thong_minh`
- Do NOT save screenshots to disk by default (no `data/screenshots/` in this phase)
- `.env` is gitignored — `ENABLE_SCREEN_VISION` flag is non-sensitive

## Next Steps

- Phase 3 (Spotify) is independent — can be developed in parallel after this phase
- Future: add `nhin_webcam()` variant (Phase 2+ scope, NOT this phase — YAGNI)
- Future: optional `SCREEN_VISION_SAVE_DIR` to persist screenshots for debugging

## Unresolved Questions

1. Is `mss>=9.0` compatible with Python 3.14? (Must test in project venv before coding)
2. Does `Pillow>=10.3` have known issues on Windows 10 with Python 3.14? (Check PyPI release notes)
3. Should `detail: "low"` or `"auto"` be used? ("low" cheaper but may miss small text — configurable via env var?)
4. Multi-monitor setup: should tool capture all monitors or only primary? (Current plan: primary only)
