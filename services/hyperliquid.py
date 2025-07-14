from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from config.settings import SETTINGS

# Initialize clients
info_client = Info(SETTINGS.get("api_url", None), skip_ws=True)
exchange = Exchange(
    SETTINGS["agent_key"],  # agent private key
    SETTINGS.get("api_url", None),
    account_address=SETTINGS["master_address"]
)

def get_positions():
    return info_client.user_state(SETTINGS["master_address"])["assetPositions"]

def market_order(coin: str, side: str, size: float):
    if SETTINGS["debug"]:
        print(f"[DEBUG] Simulated ORDER: {side.upper()} {size} {coin}")
        return {"simulated": True}

    return exchange.order(
        coin + "-PERP",               # e.g., "ETH-PERP"
        side == "buy",                # is_buy
        size,                         # quantity
        0,                            # market order
        {"limit": {"tif": "Ioc"}}    # Ioc type
    )
