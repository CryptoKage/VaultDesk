import asyncio
import json
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from services.history_loader import load_eth_ohlc
from services.vault import get_vault_status
from services.price_aggregator import aggregate_all, fetch_gecko_price
from services.hyperliquid import get_positions
from strategies.ema_cross import EMAStrategy
from config.settings import SETTINGS

app = FastAPI()
connections: set[WebSocket] = set()
strategy_task = None

@app.on_event("startup")
async def start_broadcast_loop():
    async def loop():
        while True:
            try:
                pos = get_positions()
                await broadcast({"type": "positions", "data": pos})
            except Exception as e:
                print("🔴 Broadcast error:", e)
            await asyncio.sleep(5)
    asyncio.create_task(loop())

@app.get("/api/positions")
async def api_positions():
    try:
        return JSONResponse({"positions": get_positions()})
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
async def api_vault():
    try:
        return JSONResponse({"vault": get_vault_status()})
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
async def set_strategy_config(config: dict):
    SETTINGS["strategy"] = config
    SETTINGS["stop_signal"] = False
    return JSONResponse({"status": "success", "config": config})

async def strat_runner():
    strat = EMAStrategy(**SETTINGS["strategy"])
    uri = "wss://api.hyperliquid.xyz/ws"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"method":"subscribe","topic":"book","params":{"coin":"ETH"}}))
        async for msg in ws:
            data = json.loads(msg).get("data")
            if data and "mark" in data:
                sig = strat.update_price(time.time(), float(data["mark"]))
                if sig == "long":
                    await ...  # market_order
                if SETTINGS.get("stop_signal"):
                    break

@app.post("/api/strategy/start")
async def start_strategy():
    global strategy_task
    if strategy_task and not strategy_task.done():
        return {"status":"already running"}
    strategy_task = asyncio.create_task(strat_runner())
    return {"status": "started"}

@app.post("/api/strategy/stop")
async def stop_strategy():
    SETTINGS["stop_signal"] = True
    return {"status": "stopping"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    print("⚡ WS connected:", ws.client)
    try:
        await ws.send_json({"type": "positions", "data": get_positions()})
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        connections.remove(ws)
        print("❌ Disconnected:", ws.client)

async def broadcast(msg: dict):
    dead = set()
    for ws in connections:
        try:
            await ws.send_json(msg)
        except:
            dead.add(ws)
    connections.difference_update(dead)

html = """<!DOCTYPE><body>
<script>
 const ws=new WebSocket("ws://localhost:8000/ws");
 ws.onopen=()=>console.log("✅ WS connected!");
 ws.onmessage=e=>console.log("📡 WS update:",JSON.parse(e.data));
 ws.onclose=()=>console.log("❌ WS closed");
</script><h1>Trading Desk Admin</h1><p>Open console.</p>
</body>"""

@app.get("/")
async def index():
    return HTMLResponse(html)
