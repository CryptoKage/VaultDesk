import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from services.history_loader import load_eth_ohlc
from services.vault import get_vault_status
from services.price_aggregator import aggregate_prices, aggregate_all
from services.hyperliquid import get_positions
from strategies.ema_cross import EMAStrategy
from config.settings import SETTINGS

app = FastAPI()
connections: set[WebSocket] = set()

@app.get("/api/positions")
async def api_positions():
    try:
        pos = get_positions()
        return JSONResponse({"positions": pos})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/history")
async def api_history(days: int = 60):
    df = load_eth_ohlc(days=days)
    return JSONResponse({"history": df.to_dict(orient="records")})

@app.get("/api/vault")
async def api_vault():
    try:
        vault = get_vault_status()
        return JSONResponse({"vault": vault})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/prices")
async def api_prices():
    symbols = ["ethereum", "bitcoin"]
    latest = {s: aggregate_prices(s) for s in symbols}
    aggregated = await aggregate_all(symbols)
    return {"latest": latest, "aggregated": aggregated}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    try:
        # Immediately send positions
        await ws.send_json({"type": "positions", "data": get_positions()})
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connections.remove(ws)

async def broadcast(msg: dict):
    dead = set()
    for ws in connections:
        try:
            await ws.send_json(msg)
        except:
            dead.add(ws)
    connections.difference_update(dead)

# Test HTML page
html = """
<!DOCTYPE html>
<html><body>
<script>
  const ws = new WebSocket("ws://localhost:8000/ws");
  ws.onopen = () => console.log("✅ WS connected");
  ws.onmessage = e => console.log("📡 WS update:", JSON.parse(e.data));
</script>
<h1>Trading Desk Admin</h1>
<p>Check console for live updates from /ws.</p>
</body></html>
"""

@app.get("/")
async def index():
    return HTMLResponse(html)
