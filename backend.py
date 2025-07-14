import asyncio, json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from services.hyperliquid import get_positions
from strategies.ema_cross import EMAStrategy
from config.settings import SETTINGS

app = FastAPI()
connections: set[WebSocket] = set()

# WebSocket endpoint for admin UI clients
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("⚡ New WS client connected:", ws.client)
    connections.add(ws)
    try:
        pos = get_positions()
        print("📤 Sent initial positions to client")
        await ws.send_json({"type": "positions", "data": pos})

        while True:
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print("🚪 WS client disconnected:", ws.client)
        connections.remove(ws)

# Broadcast helper to relay messages to all connected clients
async def broadcast(msg: dict):
    dead = []
    for ws in connections:
        try:
            await ws.send_json(msg)
        except Exception as e:
            print("❌ Broadcast failed to a client:", e)
            dead.append(ws)
    for ws in dead:
        print("🧹 Removing dead client:", ws.client)
        connections.remove(ws)

# HTML test page to verify WebSocket connectivity
html = """
<!DOCTYPE html>
<html><body>
<script>
  const ws = new WebSocket("ws://localhost:8000/ws");
  ws.onopen = () => console.log("✅ WS connected!");
  ws.onerror = (e) => console.error("❌ WS error:", e);
  ws.onclose = (e) => console.warn("⚠️ WS closed:", e);
  ws.onmessage = e => console.log("📡 WS update:", JSON.parse(e.data));
</script>
<h1>WebSocket Test</h1>
<p>Check the browser console and terminal logs for debug info.</p>
</body></html>
"""

@app.get("/")
async def index():
    return HTMLResponse(html)
