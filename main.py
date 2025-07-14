import asyncio
import json
import time
import websockets
from config.settings import SETTINGS
from services.hyperliquid import get_positions, market_order
from strategies.ema_cross import EMAStrategy
from backend import broadcast  # Ensure backend.py includes broadcast()

async def runner():
    print("=== Trading Desk Runner ===")
    print("Environment:", SETTINGS["env"])
    print("Master Wallet:", SETTINGS["master_address"])

    try:
        positions = get_positions()
    except Exception as e:
        print("⚠️ Error fetching positions:", e)
        positions = []
    print("Initial positions:", positions)
    asyncio.create_task(broadcast({"type": "positions", "data": positions}))

    strat = EMAStrategy(
        fast=8, slow=24, direction="both",
        stop_loss_pct=0.01, take_profit_pct=0.02
    )
    uri = "wss://api.hyperliquid.xyz/ws"
    backoff = 1

    async def send_heartbeat(ws):
        """Ping server every 20 seconds to prevent idle disconnect."""
        while True:
            await asyncio.sleep(20)
            try:
                pong = await ws.ping()
                await asyncio.wait_for(pong, timeout=10)
            except:
                break  # Exit if ping fails or ws is closed

    while True:
        try:
            async with websockets.connect(uri, ping_interval=None) as ws:
                print("🔌 WS connected; subscribing to ETH")
                await ws.send(json.dumps({
                    "method": "subscribe", "topic": "book", "params": {"coin": "ETH"}
                }))
                print("📡 Subscribed to ETH market data")

                heartbeat = asyncio.create_task(send_heartbeat(ws))
                backoff = 1  # reset backoff after successful connection

                async for msg in ws:
                    try:
                        raw = json.loads(msg)
                    except json.JSONDecodeError:
                        continue

                    data = raw.get("data")
                    if not data or "mark" not in data:
                        continue

                    ts = int(time.time())
                    mark = float(data["mark"])
                    asyncio.create_task(broadcast({"type": "tick", "timestamp": ts, "price": mark}))
                    print(f"📈 Tick {ts}: {mark}")

                    sig = strat.update_price(ts, mark)
                    if sig:
                        print(f"⚡ SIGNAL → {sig.upper()} at {mark}")
                        resp = market_order("ETH", sig, 1.0)
                        asyncio.create_task(broadcast({"type": "signal", "signal": sig, "price": mark}))
                        print("Order response:", resp)

                heartbeat.cancel()

        except websockets.ConnectionClosedOK:
            print("✨ WS closed cleanly. Reconnecting after delay...")
            await asyncio.sleep(5)

        except Exception as e:
            print(f"⚠️ WS error: {e}. Reconnecting after {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

if __name__ == "__main__":
    asyncio.run(runner())
