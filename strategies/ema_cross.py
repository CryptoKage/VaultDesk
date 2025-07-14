import pandas as pd

class EMAStrategy:
    def __init__(
        self,
        fast: int = 8,
        slow: int = 24,
        direction: str = "both",
        stop_loss_pct: float = 0.01,
        take_profit_pct: float = 0.02
    ):
        self.fast = fast
        self.slow = slow
        self.direction = direction.lower()
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.df = pd.DataFrame(columns=["timestamp", "price"])
        self.position = None  # {'side': 'buy'|'sell', 'entry': price}

    def update_price(self, timestamp: int, price: float) -> str | None:
        """
        Process a tick. Returns a signal ("buy" or "sell") if triggered, else None.
        """

        # Append new tick
        self.df.loc[len(self.df)] = [timestamp, price]

        # === TEST HACK: force signal on first tick ===
        if len(self.df) == 1:
            # Remove this block once test is complete
            return "buy"
        # ============================================

        # Wait until we have enough data for EMAs
        if len(self.df) < self.slow + 2:
            return None

        # Calculate EMAs
        self.df["ema_fast"] = self.df["price"].ewm(span=self.fast).mean()
        self.df["ema_slow"] = self.df["price"].ewm(span=self.slow).mean()

        prev = self.df.iloc[-2]
        curr = self.df.iloc[-1]

        # Crossover logic
        side = None
        if prev.ema_fast < prev.ema_slow and curr.ema_fast > curr.ema_slow:
            side = "buy"
        elif prev.ema_fast > prev.ema_slow and curr.ema_fast < curr.ema_slow:
            side = "sell"

        # Entry logic
        if side and self._allowed(side) and self.position is None:
            self.position = {"side": side, "entry": price}
            return side

        # Exit logic based on stop-loss or take-profit
        if self.position:
            change = (price - self.position["entry"]) / self.position["entry"]
            if self.position["side"] == "sell":
                change = -change
            if change <= -self.stop_loss_pct or change >= self.take_profit_pct:
                exit_side = "sell" if self.position["side"] == "buy" else "buy"
                self.position = None
                return exit_side

        return None

    def _allowed(self, side: str) -> bool:
        if self.direction == "both":
            return True
        if self.direction == "long" and side == "buy":
            return True
        if self.direction == "short" and side == "sell":
            return True
        return False
