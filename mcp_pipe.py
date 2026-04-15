import asyncio
import json
import os
from pathlib import Path

import websockets

# Load .env if present (no external dep)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value

WSS_URL = os.getenv("XIAOZHI_MCP_WSS")
if not WSS_URL:
    raise RuntimeError(
        "XIAOZHI_MCP_WSS not set. Add to .env: "
        "XIAOZHI_MCP_WSS=wss://api.xiaozhi.me/mcp/?token=YOUR_TOKEN"
    )

def patch_response(raw: str) -> str:
    try:
        msg = json.loads(raw)
        result = msg.get("result", {})
        structured = result.get("structuredContent")
        if not structured:
            return raw

        # Xử lý messages_read — chỉ giữ role + text
        if "messages" in structured:
            simplified = []
            for m in structured["messages"]:
                role = m.get("role", "")
                if role in ("assistant", "user"):
                    texts = []
                    for c in m.get("content", []):
                        if c.get("type") == "text":
                            texts.append(c["text"])
                    if texts:
                        sender = m.get("senderLabel", role)
                        simplified.append(f"[{sender}]: {' '.join(texts)}")
            result["content"] = [{"type": "text", "text": "\n\n".join(simplified)}]

        # Xử lý conversations_list
        elif "conversations" in structured:
            convs = []
            for c in structured["conversations"]:
                convs.append({
                    "sessionKey": c.get("sessionKey"),
                    "displayName": c.get("displayName"),
                    "lastMessage": c.get("lastMessagePreview", "")[:200]
                })
            result["content"] = [{"type": "text", "text": json.dumps(convs, ensure_ascii=False)}]

        msg["result"] = result
        return json.dumps(msg, ensure_ascii=False)
    except Exception:
        pass
    return raw

async def main():
    import sys
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    print(f"✅ MCP server spawned PID: {proc.pid}")

    async with websockets.connect(WSS_URL) as ws:
        print("✅ Đã kết nối Xiaozhi")

        async def stderr_logger():
            while True:
                line = await proc.stderr.readline()
                if line:
                    print(f"🔴 stderr: {line.decode('utf-8', errors='replace').strip()}")

        async def xiaozhi_to_mcp_server():
            async for msg in ws:
                # Intercept ping requests — respond directly from bridge
                # with a NON-empty result so that cloud LLM (if reading the
                # stream) doesn't misinterpret `result:{}` as "no data".
                try:
                    parsed = json.loads(msg)
                    if parsed.get("method") == "ping":
                        pong = json.dumps({
                            "jsonrpc": "2.0",
                            "id": parsed.get("id"),
                            "result": {"keepalive": True, "alive": "ok"},
                        })
                        print(f"💓 ping id={parsed.get('id')} → pong (non-empty, handled by bridge)")
                        await ws.send(pong)
                        continue
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
                print(f"📨 Xiaozhi → MCP: {msg}")
                proc.stdin.write((msg + "\n").encode())
                await proc.stdin.drain()

        async def mcp_server_to_xiaozhi():
            while True:
                line = await proc.stdout.readline()
                if line:
                    patched = patch_response(line.decode("utf-8", errors="replace").strip())
                    print(f"📤 MCP → Xiaozhi: {patched}")
                    await ws.send(patched)

        await asyncio.gather(
            stderr_logger(),
            xiaozhi_to_mcp_server(),
            mcp_server_to_xiaozhi()
        )

asyncio.run(main())