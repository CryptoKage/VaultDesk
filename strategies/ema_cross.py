    def __init__(self):
        self.df = pd.DataFrame(columns=["timestamp", "price"])
        self.position = None

    def update_price(self, timestamp, price):
        self.df.loc[len(self.df)] = [timestamp, price]
        if len(self.df) < 24:
            return None
        self.df["ema8"] = self.df["price"].ewm(span=8).mean()
        self.df["ema24"] = self.df["price"].ewm(span=24).mean()
        return self.signal()

    def signal(self):
        e8_prev, e8 = self.df["ema8"].iloc[-2:]
        e24_prev, e24 = self.df["ema24"].iloc[-2:]
        if e8_prev < e24_prev and e8 > e24:
            return "buy"
        elif e8_prev > e24_prev and e8 < e24:
            return "sell"
        return None