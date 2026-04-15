# Jarvis Features Research - Techla Assistant (Xiaozhi/ESP32-S3 Stack)

**Date:** 2026-04-15
**Stack:** Python 3.14 / FastMCP / Xiaozhi cloud STT+TTS+LLM / ESP32-S3 / Windows PC

---

## TL;DR - Top 5 Features (Impact x Feasibility)

| Rank | Feature | Why |
|------|---------|-----|
| 1 | **Semantic Memory Upgrade (mem0)** | memory_kg.py is keyword-lookup only; mem0 adds vector search + auto-extraction. 2-3h, free. |
| 2 | **Proactive Scheduler (APScheduler)** | Cron + Telegram/WSS inject. Device speaks first. ~4h work. |
| 3 | **Vision / Screen Awareness (GPT-4o Vision + mss)** | Screenshot to GPT-4o. One tool file. 2-3h. ~$0.01/call. |
| 4 | **Spotify Music (spotipy)** | HA wires lights; Spotify adds music. Full ambient control. ~3h. |
| 5 | **Personality Layer (system prompt)** | Zero code change. Huge demo impact. 1h work. |

---

## Feature 1: Persistent Memory and Personalization

**What Jarvis does:** Recalls preferences, projects, history without being told twice.

**Current state:** tools/memory_kg.py - plain JSON, exact-key lookup. No semantic search.

**Recommended:** mem0 OSS self-hosted
- Repo: https://github.com/mem0ai/mem0
- Stars: ~28k | Last commit: April 2025 (active weekly)
- Backend: ChromaDB or Qdrant locally on Windows
- LOCOMO benchmark: 26% above OpenAI memory, 91% faster than naive RAG

**vs. alternatives:**
- ChromaDB + custom: 3x code for same result. YAGNI.
- Letta/MemGPT: full agent framework for one feature. Overkill.

**Integration:** tools/memory_semantic.py (replaces memory_kg.py)
```python
@mcp.tool()
def remember(entity: str, fact: str) -> str:
    mem.add(f"{entity}: {fact}", user_id="tony")
    return "Remembered."

@mcp.tool()
def recall(query: str) -> str:
    results = mem.search(query, user_id="tony", limit=5)
    return "
".join(r["memory"] for r in results["results"])
```

**Cost:** Free. ChromaDB local. No API key.
**Effort:** 2-3h (install + wrap tools + migrate existing JSON).
**Risks:**
- Python 3.14 compat: mem0ai pins chromadb<0.6 (pydantic v1). Test before committing.
- Cold-start embedding ~1-2s on first query.
- Windows: use absolute path for ChromaDB persist dir.

---

## Feature 2: Proactive Behavior - Jarvis Initiates

**What Jarvis does:** Speaks without being asked. Alerts and reminders proactively.

**Core problem:** MCP is pull-only. No native push from Python server to ESP32.

**Two-tier workaround:**

Tier A - Telegram push (already wired, zero new infra):
telegram_bot.py exists. BackgroundScheduler calls Telegram API directly (not via MCP).
User gets phone notification. Works today.

Tier B - Xiaozhi WSS inject (experimental):
mcp_pipe.py holds open WSS to Xiaozhi. Background thread injects synthetic message into
stdio pipe. Xiaozhi processes as user speech, LLM responds, TTS plays on ESP32.
NOT officially supported but plausible given mcp_pipe.py bridges stdin/stdout.

**Library:** APScheduler 3.x
- Repo: https://github.com/agronholm/apscheduler
- Stars: ~13k | Last commit: March 2025
- BackgroundScheduler: runs in same Python process as MCP server

**Integration:** tools/proactive_scheduler.py
```python
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")

@mcp.tool()
def schedule_reminder(message: str, cron: str) -> str:
    scheduler.add_job(lambda: _push_alert(message), "cron", **_parse_cron(cron))
    return f"Scheduled: {message}"
```

**Cost:** Free. **Effort:** 4h.
**Risks:**
- WSS inject is a hack; Xiaozhi protocol updates can break it.
- Use SQLiteJobStore for job persistence across restarts.
- Specify timezone explicitly; Windows system TZ unreliable in Python.

---

## Feature 3: Vision / Screen Awareness

**What Jarvis does:** Sees screen, analyzes environment on demand.

**Options ranked:**

| Option | Latency | Cost/call | Local? | Effort |
|--------|---------|-----------|--------|--------|
| GPT-4o Vision screenshot (RECOMMENDED) | 350-700ms | ~$0.005 | No | 1-2h |
| GPT-4o Vision webcam | 700-1200ms | ~$0.01 | No | 2-3h |
| Gemini 1.5 Flash Vision | ~500ms | free tier | No | 2-3h |
| moondream2 local VLM 1.8B | ~800ms | free | Yes | 5h |

**Recommended:** GPT-4o Vision on-demand screenshot (no webcam required)
- mss: pure Python, Windows-native, no DLL deps
- Pillow>=10.3 for resize/compress
- OpenAI SDK already in stack

**Integration:** tools/vision_awareness.py
```python
import mss, base64, io
from PIL import Image
from openai import OpenAI

@mcp.tool()
def see_screen(question: str = "What is on the screen?") -> str:
    with mss.mss() as sct:
        img = sct.grab(sct.monitors[1])
    pil = Image.frombytes("RGB", img.size, img.rgb)
    pil.thumbnail((1280, 720))
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=75)
    b64 = base64.b64encode(buf.getvalue()).decode()
    resp = OpenAI().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": question},
        ]}],
        max_tokens=300,
    )
    return resp.choices[0].message.content
```

**Cost:** ~$0.005-0.01/call. 10 calls/day = ~$3/month.
**Effort:** 2-3h.
**Risks:**
- Privacy: all open windows visible. Add disclaimer in docstring.
- monitors[1] = primary; monitors[0] = virtual combined.
- mss works without admin on Windows 10.

---## Feature 4: Smart Home + Music
Three unread messages and a meeting at 3pm, Sir.

## Feature 4: Smart Home + Music (HA Done; Gap = Spotify)

**What Jarvis does:** Lights, music, climate in one voice command.
**Current state:** home_assistant.py fully wired for lights/switches/climate.
**Gap:** Music control. spotipy 2.25.x:
- Repo: https://github.com/spotipy-dev/spotipy
- Stars: ~5.5k | Last commit: Feb 2025
- OAuth PKCE for desktop, no web server needed
- Spotify Premium required for playback control (free = browse only)

**Integration:** tools/music_spotify.py
```python
@mcp.tool()
def play_music(query: str, device_name: str = "") -> str:
    """Play music on Spotify. query = artist, song, genre, or mood."""
    sp = _get_client()
    results = sp.search(q=query, type="track,playlist", limit=3)
    uri = results["tracks"]["items"][0]["uri"]
    sp.start_playback(uris=[uri])
    return "Playing: " + results["tracks"]["items"][0]["name"]
```

**Demo command:** Play lo-fi and dim office to 40%
LLM calls play_music() + dieu_khien_thiet_bi() in sequence.
**Cost:** Spotify Premium ~$5-10/month. **Effort:** 3h.
**Risks:** Active Spotify Connect device required. localhost:8080 OAuth callback once during setup.

---

## Feature 5: Personality Layer

**What Jarvis does:** Dry wit, confident, calls user Sir, never hedges.
**No library needed.** Pure system prompt engineering.

Approach A (preferred): Xiaozhi cloud system prompt. Configure in dashboard. Zero code change.
Approach B: Extend tools/company.py with PERSONA constant.

**Sample prompt:**
```
You are Techly, an AI in the style of J.A.R.V.I.S. from Iron Man.
Personality: brilliant, dry wit, unfailingly polite, calls user Sir or by name.
Style: concise, confident, occasionally sardonic. Answer first, caveats last.
Never say I am just an AI. When joking: one dry line, then move on.
```

**Cost:** Free. **Effort:** 1h.
**Risk:** Xiaozhi system prompt char limit unknown. Test 300-char version first.

---

## Feature 6: Calendar / Email

**What Jarvis does:** Three unread messages and a meeting at 3pm.

**Current state:** calendar_gcal.py exists (GOOGLE_ACCESS_TOKEN env-gated).
**Gap:** Gmail read. Add gmail.readonly scope to existing OAuth. Same credentials.
Library: google-api-python-client (official, ~8k stars, Google-maintained).

**Integration:** tools/gmail_reader.py
```python
@mcp.tool()
def read_emails(max_results: int = 5, unread_only: bool = True) -> str:
    """Read recent Gmail inbox emails. Uses same OAuth as calendar_gcal.py."""
    ...
```

**Cost:** Free (Google API, 1B quota/day).
**Effort:** 2h if gcal OAuth working; 5h from scratch.
**Risk:** One-time localhost OAuth callback during setup.

---

## Feature 7: Speaker Recognition (ARCHITECTURALLY BLOCKED)

**Library evaluated:** pyannote.audio 3.3 | Stars: ~7k | Last commit: March 2025
Model: pyannote/speaker-diarization-community-1 (free, local, no gating, HuggingFace)
Hardware: RTX 3060/4060 with 6-8GB VRAM sufficient for hobby

**Hard blocker for this stack:**
Xiaozhi cloud processes raw ESP32 audio. Only transcribed TEXT reaches Python MCP server.
Raw PCM is never forwarded. pyannote needs PCM input.
Bypass requires ESP32 firmware modification or a second dedicated local mic.
Both out-of-scope for hobby single-user setup.

See Anti-recommendations.

---

## Feature 8: Real-time Awareness (Stocks / News Alerts)

**Current state:** weather.py, news.py, finance.py all exist and work.
**Gap:** Proactive threshold push (stock drops >5%, breaking news).

**Solution:** Add watchers to APScheduler from Feature 2:
```python
scheduler.add_job(check_portfolio_alerts, "interval", minutes=30)
scheduler.add_job(check_breaking_news, "interval", minutes=15)
```

Libraries: yfinance (implied by finance.py), newsapi-python (free 100 calls/day).
**Cost:** Free tiers. **Effort:** 1-2h on top of APScheduler setup.

---

## Roadmap (Max Demo Impact Order)

```
Phase 1 - Wow Factor (~10h total):
  Step 1: Personality system prompt (1h)    -> immediate Jarvis feel, zero risk
  Step 2: Screen vision tool (2-3h)         -> see_screen() demo is a showstopper
  Step 3: Spotify music (3h)                -> voice-controlled music

Phase 2 - Proactive Intelligence (~6h total):
  Step 4: APScheduler + Telegram push (4h)  -> device speaks first = true Jarvis
  Step 5: Stock/news threshold alerts (2h)  -> rides on Step 4 infrastructure

Phase 3 - Deep Memory and Context (~5h total):
  Step 6: mem0 semantic memory (3h)  -> replaces memory_kg.py
  Step 7: Gmail reader (2h)          -> rides on existing gcal OAuth
```

Total: ~21h for full Jarvis demo kit. Phase 1 alone (10h) delivers 80% of wow factor.

---

## Anti-Recommendations

| Feature | Why Not |
|---------|---------|
| Speaker recognition (pyannote) | ESP32 audio to Xiaozhi cloud; raw PCM never reaches Python server. Architecturally blocked. |
| Local LLM (Ollama/LM Studio) | GPT-5 via Xiaozhi is world-class. Local = 8-16GB RAM + 10s latency + worse quality. YAGNI. |
| Custom wake-word (Porcupine/Vosk) | Xiaozhi handles on ESP32. Duplicate = confusion + doubled resource use. |
| Continuous webcam feed | 2-4 fps to GPT-4o = $30-120/month. On-demand screenshot = $3/month. Same utility. |
| Custom TTS replacement | Xiaozhi TTS is good. Replacing requires routing audio back to PC. High effort, marginal gain. |
| mem0 cloud paid tier | Self-hosted OSS + local ChromaDB does the same for free. |

---

## Unresolved Questions

1. Xiaozhi WSS inject feasibility: Can mcp_pipe.py inject synthetic messages without breaking handshake? Needs empirical test.
2. calendar_gcal.py OAuth: Is token refresh implemented or scaffolded? Determines Gmail effort (2h vs 5h).
3. Xiaozhi system prompt config: Where in dashboard? Character limit unknown.
4. Python 3.14 + mem0 compat: mem0ai pins chromadb<0.6 (pydantic v1). Needs explicit test.
5. Spotify Premium: Required for playback. Free tier = browse/search only.

---

## Sources

- [mem0 GitHub](https://github.com/mem0ai/mem0)
- [mem0 MCP - PulseMCP](https://www.pulsemcp.com/servers/coleam00-mem0)
- [ChromaDB MCP - Skywork](https://skywork.ai/skypage/en/chromadb-mcp-server-ai-memory/1980089070183030784)
- [MemPalace vs mem0 analysis](https://gist.github.com/roman-rr/0569fc487cc620f54a70c90ab50d32e3)
- [pyannote/pyannote-audio GitHub](https://github.com/pyannote/pyannote-audio)
- [pyannote HuggingFace](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [Xiaozhi ESP32 GitHub](https://github.com/78/xiaozhi-esp32)
- [Xiaozhi MCP DEV.to](https://dev.to/david_thomas/building-a-diy-esp32-s3-ai-voice-assistant-with-xiaozhi-mcp-2jjp)
- [APScheduler GitHub](https://github.com/agronholm/apscheduler)
- [spotipy GitHub](https://github.com/spotipy-dev/spotipy)
- [GPT-4o Vision 2025 - Skywork](https://skywork.ai/blog/agent/openai-realtime-gpt-4o-vision-build-multimodal-voice-agents-2025/)
- [WebcamGPT-Vision GitHub](https://github.com/bdekraker/WebcamGPT-Vision)

---

**Status:** DONE
**Summary:** 8 features analyzed; 5 immediately buildable (personality, vision, music, proactive, semantic memory) within ~21h total. Speaker recognition blocked by Xiaozhi cloud audio routing. Phase 1 (10h) delivers 80% of wow factor.
**Concerns:** WSS inject for proactive push is speculative - validate Xiaozhi protocol before investing. Python 3.14 + mem0 compat needs explicit test before upgrading.