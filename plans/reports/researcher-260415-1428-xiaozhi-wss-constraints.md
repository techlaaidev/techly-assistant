---
title: Xiaozhi WSS/MCP Protocol Constraint Analysis
date: 2026-04-15
---

# Xiaozhi WSS/MCP Protocol Constraint Analysis

## 1. TL;DR Verdict Table

| Feature | Verdict | Notes |
|---|---|---|
| WSS speaks vanilla JSON-RPC 2.0 MCP | WORKS | Standard spec |
| Tool calls: cloud calls MCP server | WORKS | Cloud is MCP client |
| mcp_pipe.py bridge pattern | WORKS | Correct architecture |
| Server-initiated TTS to device (proactive) | BLOCKED | No cross-layer bridge |
| stderr JSON hack triggers device TTS | LIKELY BLOCKED | ~5% chance |
| Proactive push via Telegram | WORKS | telegram_bot.py already in repo |
| System prompt on dashboard | WORKS WITH CAVEAT | Char limit unknown |
| Screen vision / Spotify (PC tools) | WORKS | Normal tool-call round-trip |

---

## 2. Protocol Analysis

### 2.1 Two-Layer Architecture (Critical)

Xiaozhi has TWO distinct protocol layers with NO bridge between them:

    Layer A  ESP32 <-WSS-> xiaozhi.me cloud
      Protocol: Custom Xiaozhi WebSocket Protocol
      Messages: type=hello, type=listen, type=stt, type=tts, binary Opus frames

    Layer B  xiaozhi.me cloud <-WSS-> mcp_pipe.py
      Protocol: Standard JSON-RPC 2.0 MCP over WebSocket
      Messages: initialize, tools/list, tools/call, ping, notifications/*

mcp_pipe.py operates ONLY on Layer B. No access to Layer A audio/TTS.

### 2.2 JSON-RPC 2.0 Compliance

Confirmed via official mcp-protocol.md: "internal structure follows JSON-RPC 2.0 specification."
Methods: initialize, tools/list, tools/call, ping.
mcp_pipe.py ping handler (lines 106-114): correct.

### 2.3 Message Direction

Layer B (MCP side):
- Cloud -> MCP server: initialize, tools/list, tools/call, ping  [cloud is CLIENT]
- MCP server -> Cloud: responses + optional notifications/* (no id field)

Layer A (Device side):
- Cloud -> Device: type:tts audio, type:stt text, type:llm emotion
- Device -> Cloud: audio frames, type:listen, type:hello

CRITICAL GAP: Xiaozhi cloud acts as firewall between Layer B and Layer A.
No sanctioned API for MCP server to inject audio into device TTS stream.

---

## 3. Per-Question Verdicts

### Q1: WSS Protocol [CRITICAL] - WORKS

Protocol is vanilla JSON-RPC 2.0. Official mcp-protocol.md confirms standard spec.
wss://api.xiaozhi.me/mcp/?token=... endpoint: cloud = MCP client, mcp_pipe.py = MCP server.
Cloud CALLS tools/call; server RESPONDS. Bidirectional WSS but pull-based semantics.
MCP notifications (no id) allowed by spec; cloud handling of server-push undocumented.
Source: github.com/78/xiaozhi-esp32 docs/mcp-protocol.md, docs/mcp-usage.md

### Q2: Proactive Push - Server Trigger Cloud TTS? [CRITICAL] - BLOCKED

Architectural block, not a bug:
1. Cloud is MCP CLIENT (pull model). Only calls mcp_pipe.py when user speaks. No listener.
2. JSON-RPC notifications from server to cloud: spec allows; cloud handling undocumented.
3. No REST/HTTP push endpoint documented for xiaozhi.me cloud.
4. MQTT workaround requires self-hosted backend (xinnan-tech). Not available with stock cloud.

The stderr_to_xiaozhi hack (mcp_pipe.py lines 88-96):
- Sends JSON over WSS to cloud when server prints JSON to stderr
- Cloud likely IGNORES it (it is the client, not a listener for server-push)
- Probability of triggering TTS: ~5% (requires undocumented cloud feature)
- NEEDS one empirical test before relying on or removing

Source: websocket.md (layer separation), mcp-usage.md (pull model), deepwiki.com/xinnan-tech

### Q3: Dashboard System Prompt [MEDIUM] - WORKS WITH CAVEAT

Dashboard confirmed at xiaozhi.me -> agent settings.
System prompt injected into every LLM call on cloud.
Char limit: UNKNOWN. No official docs, no community reports with specific number.
Phase 1 plan correctly handles this (test 300-char first, fallback to company_data.md).
Action: paste 300/500/1000-char text, observe truncation empirically.

### Q4: Alternative Proactive Channels [MEDIUM] - WORKS

Ranked options:
1. Telegram Bot (BEST): telegram_bot.py already in repo. POST Bot API sendMessage. Zero new infra.
2. Discord Bot: heavier setup (intents, slash cmds), less ideal for mobile push
3. SMS/Twilio: per-message cost, overkill
4. Signal: no official bot API

Minimal implementation to add in tools/telegram_bot.py:

    def send_proactive(text: str) -> None:
        TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )

Protocol hack (inject fake user utterance into cloud): no mechanism. Blocked.

### Q5: Screen Vision and Spotify [LOW] - WORKS

Normal MCP round-trip: user speaks -> cloud STT -> LLM -> tools/call -> PC tool -> text -> TTS -> ESP32.
No firmware dependency.
Caveat: vision tool latency 3-8s may hit cloud timeout. Monitor in testing.

---

## 4. Plan Impact (List Only - Do Not Edit)

**phase-01-personality-layer.md**
- No structural change needed.
- Add note: char limit empirical test is blocking step before pasting prompt.

**phase-02-screen-vision.md**
- Confirmed unblocked. No changes.

**phase-03-spotify-control.md**
- Confirmed unblocked. No changes.

**mcp_pipe.py lines 88-96 (stderr_to_xiaozhi)**
- Empirical test needed. If cloud ignores: remove to reduce noise.
- Test: print deliberate notification JSON from server.py stderr, check if ESP32 speaks.

---

## 5. Recommended Alternative Architecture (Proactive Blocked)

    Current (reactive only):
      User speaks -> ESP32 -> Xiaozhi cloud -> MCP server -> response -> TTS -> ESP32

    Recommended (adds proactive channel via Telegram):
      Background event -> server.py triggers send_proactive(text)
      -> POST api.telegram.org/bot{TOKEN}/sendMessage
      -> User phone receives Telegram notification
      User reads, says "Techly, read that aloud" -> normal reactive loop

KISS/YAGNI: no new infra, existing bot token, immediate value.

---

## 6. Unresolved Questions (Empirical Tests Required)

1. [HIGH] Does xiaozhi.me cloud act on JSON notifications pushed from mcp_pipe.py over WSS?
   Test: print notification JSON to server.py stderr, check if ESP32 speaks anything.

2. [HIGH] Exact char limit of system prompt field on xiaozhi.me dashboard?
   Test: paste 300/500/1000 chars, observe truncation.

3. [MEDIUM] Does xiaozhi.me have undocumented REST API for push-to-device?
   Test: browser devtools Network tab while logged into dashboard.

4. [MEDIUM] Cloud timeout threshold for high-latency tool calls (vision ~5-8s)?
   Test: deliberate sleep in tool, observe if cloud waits or errors.

5. [LOW] Does cloud forward MCP JSON-RPC errors back as voice error messages?
   Test: return intentional error from server.py, listen to ESP32.

---

## Sources

- [78/xiaozhi-esp32 mcp-protocol.md](https://github.com/78/xiaozhi-esp32/blob/main/docs/mcp-protocol.md)
- [78/xiaozhi-esp32 mcp-usage.md](https://github.com/78/xiaozhi-esp32/blob/main/docs/mcp-usage.md)
- [78/xiaozhi-esp32 websocket.md](https://github.com/78/xiaozhi-esp32/blob/main/docs/websocket.md)
- [xinnan-tech/xiaozhi-esp32-server DeepWiki](https://deepwiki.com/xinnan-tech/xiaozhi-esp32-server)
- [toddpan/xiaozhi-esp32-mcp](https://github.com/toddpan/xiaozhi-esp32-mcp)
- [huangjunsen0406/py-xiaozhi](https://github.com/huangjunsen0406/py-xiaozhi)
