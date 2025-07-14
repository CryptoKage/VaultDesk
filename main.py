import asyncio, json, time
import websockets
from strategies.ema_cross import EMAStrategy
from services.hyperliquid import market_order

strat = EMAStrategy()

async def runner():
    async with websockets.connect("wss://api.hyperliquid.xyz/ws") as ws:
        await ws.send(json.dumps({"method": "subscribe", "topic": "book", "params": {"coin": "ETH"}}))
        while True:
            msg = await ws.recv()
            parsed = json.loads(msg)
            try:
                mark = float(parsed['data']['mark'])
                ts = int(time.time())
                signal = strat.update_price(ts, mark)
                if signal:
                    print(f"[{ts}] SIGNAL: {signal.upper()} at {mark}")
                    market_order("ETH", signal, 1.0)
            except:
                continue

if __name__ == "__main__":
    asyncio.run(runner())
