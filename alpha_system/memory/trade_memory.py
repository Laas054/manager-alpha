import json
import os
from datetime import datetime, UTC


class TradeMemory:
    """Mémoire persistante de tous les trades."""

    def __init__(self, data_dir="alpha_system/data"):

        self.data_dir = data_dir
        self.file = os.path.join(data_dir, "trade_memory.json")
        self.trades = []

        os.makedirs(data_dir, exist_ok=True)
        self._load()

        print(f"TradeMemory initialized ({len(self.trades)} trades)")


    def record(self, market, side, price, size, pnl, confidence, model=""):

        self.trades.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "market": market,
            "side": side,
            "price": price,
            "size": size,
            "pnl": pnl,
            "confidence": confidence,
            "model": model,
            "won": pnl > 0
        })
        self._save()


    def get_avg_confidence(self, wins_only=True):

        filtered = [t for t in self.trades if t["won"] == wins_only]
        if not filtered:
            return 0
        return sum(t["confidence"] for t in filtered) / len(filtered)


    def _load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, "r") as f:
                    self.trades = json.load(f)
            except:
                self.trades = []

    def _save(self):
        try:
            with open(self.file, "w") as f:
                json.dump(self.trades, f, indent=2)
        except:
            pass
