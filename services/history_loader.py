import pandas as pd
from pycoingecko import CoinGeckoAPI

def load_eth_ohlc(days: int = 60, interval: str = "daily") -> pd.DataFrame:
    """
    Fetch historical OHLC candle data for Ethereum.
    :param days: number of past days of data
    :param interval: ignored for OHLC endpoint; daily is default
    :return: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close']
    """
    cg = CoinGeckoAPI()
    raw = cg.get_coin_ohlc_by_id(id="ethereum", vs_currency="usd", days=str(days))
    df = pd.DataFrame(raw, columns=["timestamp_ms", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    return df[["timestamp", "open", "high", "low", "close"]]
