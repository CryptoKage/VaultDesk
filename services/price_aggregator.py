import os
import asyncio
import requests
from pycoingecko import CoinGeckoAPI

# CoinMarketCap requires an API key in your environment
CMC_API_KEY = os.getenv("CMC_API_KEY")
CMC_HEADERS = {"X-CMC_PRO_API_KEY": CMC_API_KEY} if CMC_API_KEY else {}

# CryptoCompare requires an API key
CRYPTCOMPARE_KEY = os.getenv("CRYPTCOMPARE_API_KEY")
CC_HEADERS = {"Authorization": f"Apikey {CRYPTCOMPARE_KEY}"} if CRYPTCOMPARE_KEY else {}

cg = CoinGeckoAPI()

def fetch_gecko_price(symbol: str, vs="usd") -> float | None:
    try:
        data = cg.get_price(ids=symbol, vs_currencies=vs)
        return data.get(symbol, {}).get(vs)
    except Exception as e:
        print("❌ Gecko:", e)
        return None

def fetch_cmcap_price(symbol: str, vs="USD") -> float | None:
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": symbol.upper(), "convert": vs.upper()}
    try:
        resp = requests.get(url, headers=CMC_HEADERS, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()["data"][symbol.upper()]["quote"][vs.upper()]["price"]
    except Exception as e:
        print("❌ CMC:", e)
        return None

def fetch_cc_price(symbol: str, vs="USD") -> float | None:
    url = "https://min-api.cryptocompare.com/data/price"
    params = {"fsym": symbol.upper(), "tsyms": vs.upper()}
    try:
        resp = requests.get(url, headers=CC_HEADERS, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json().get(vs.upper())
    except Exception as e:
        print("❌ CryptoCompare:", e)
        return None

async def fetch_hyperliquid_metrics(pair: str):
    from services.hyperliquid import get_perpetual_info  # define in hyperliquid.py
    return get_perpetual_info(pair)

def aggregate_prices(symbol: str) -> dict:
    results = {}
    results["coin"] = symbol
    results["coingecko"] = fetch_gecko_price(symbol)
    results["cmc"] = fetch_cmcap_price(symbol)
    results["cryptocompare"] = fetch_cc_price(symbol)
    return results

async def aggregate_all(symbols: list[str]) -> dict:
    prices = {}
    tasks = []
    for s in symbols:
        tasks.append(asyncio.to_thread(aggregate_prices, s))
    metrics_task = asyncio.create_task(fetch_hyperliquid_metrics(symbols[0]))

    fetched = await asyncio.gather(*tasks, return_exceptions=True)
    metrics = await metrics_task

    for idx, s in enumerate(symbols):
        prices[s] = fetched[idx] if not isinstance(fetched[idx], Exception) else {}

    return {"prices": prices, "hyperliquid": metrics}
