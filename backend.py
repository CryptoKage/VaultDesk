import asyncio
import json
import time
from typing import Optional

import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from services.history_loader import load_eth_ohlc
from services.vault import get_vault_status
from services.price_aggregator import aggregate_all, fetch_gecko_price
from services.hyperliquid import get_positions, market_order
from strategies.ema_cross import EMAStrategy
from config.settings import SETTINGS

app = FastAPI()
connections: set[WebSocket] = set()
STRAT_TASK = None

# Pydantic model for strategy config
class StrategyConfig(BaseModel):
    vaultId: int
    config: dict

@app.get("/api/strategy")
async def get_strategy_config(vaultId: int = 1):
    cfg = SETTINGS.get("strategy", {})
    return JSONResponse({"config": cfg, "vaultId": vaultId})

@app.get("/api/positions")
async def api_positions():
    try:
        pos = get_positions()
        return JSONResponse({"positions": pos})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/history")
async def api_history(days: int = 60):
    try:
        df = load_eth_ohlc(days=days)
        return JSONResponse({"history": df.to_dict(orient="records")})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/vault")
async def api_vault(vaultId: Optional[int] = None):
    try:
        vault = get_vault_status(vaultId)
        return JSONResponse({"vault": vault})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/prices")
async def api_prices(symbol: str = "ethereum"):
    try:
        latest = fetch_gecko_price(symbol)
        aggregated = await aggregate_all([symbol])
        return JSONResponse({"latest": latest, "aggregated": aggregated})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/strategy/config")
async def set_strategy_config(payload: StrategyConfig):
    SETTINGS["strategy"] = payload.config
    return JSONResponse({"status": "success", "config": payload.config})

@app.post("/api/strategy/start")
async def start_strategy(payload: StrategyConfig):
    global STRAT_TASK
    SETTINGS["stop_signal"] = False
    if STRAT_TASK is None or STRAT_TASK.done():
        STRAT_TASK = asyncio.create_task(strat_runner())
    return JSONResponse({"status": "started"})

@app.post("/api/strategy/stop")
async def stop_strategy(payload: StrategyConfig):
    SETTINGS["stop_signal"] = True
    return JSONResponse({"status": "stopping"})

# WS broadcast loop on startup
@app.on_event("startup")
async def start_broadcast_loop():
    async def loop():
        while True:
            try:
                positions = get_positions()
                await broadcast({"type": "positions", "data": positions})
            except Exception as e:
                print("🔴 Broadcast error:", e)
            await asyncio.sleep(5)
    asyncio.create_task(loop())

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    print("⚡ New WS client connected:", ws.client)
    try:
        await ws.send_json({"type": "positions", "data": get_positions()})
        while True:
            await asyncio.sleep(30)
            if SETTINGS.get("stop_signal"):
                await ws.send_json({"type": "log", "data": "Strategy stopping"})
    except WebSocketDisconnect:
        connections.remove(ws)
        print("❌ WS client disconnected:", ws.client)

async def broadcast(msg: dict):
    to_remove = set()
    for ws in connections:
        try:
            await ws.send_json(msg)
        except:
            to_remove.add(ws)
    connections.difference_update(to_remove)

html = """
<!DOCTYPE html><body>
<script>
  const ws = new WebSocket("ws://localhost:8000/ws");
  ws.onopen = () => console.log("✅ WS connected!");
  ws.onmessage = e => console.log("📡 WS update:", JSON.parse(e.data));
  ws.onclose = () => console.log("❌ WS closed");
</script>
<h1>Trading Desk Admin</h1><p>Open console to see live WS data.</p>
</body></html>
"""

@app.get("/")
async def index():
    return HTMLResponse(html)

# Background strategy runner
async def strat_runner():
    strat_cfg = SETTINGS.get("strategy", {})
    strat = EMAStrategy(**strat_cfg)
    uri = "wss://api.hyperliquid.xyz/ws"
    backoff = 1

    async def send_heartbeat(ws):
        while True:
            await asyncio.sleep(20)
            try:
                pong = await ws.ping()
                await asyncio.wait_for(pong, timeout=10)
            except:
                break

    while not SETTINGS.get("stop_signal"):
        try:
            async with websockets.connect(uri, ping_interval=None) as ws:
                await ws.send(json.dumps({"method":"subscribe","topic":"book","params":{"coin":"ETH"}}))
                heartbeat = asyncio.create_task(send_heartbeat(ws))
                async for msg in ws:
                    data = json.loads(msg).get("data", {})
                    if "mark" not in data:
                        continue
                    ts = int(time.time())
                    mark = float(data["mark"])
                    await broadcast({"type":"tick","timestamp":ts,"price":mark})
                    sig = strat.update_price(ts, mark)
                    if sig:
                        resp = market_order("ETH", sig, 1.0)
                        await broadcast({"type":"signal","signal":sig,"price":mark})
                        if SETTINGS.get("stop_signal"):
                            break
                heartbeat.cancel()
        except Exception as e:
            print("⚠️ WS error:", e)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
