import json
import os
from datetime import datetime, UTC


class TradeMemory:

    def __init__(self, data_dir="alpha_system/data"):

        self.data_dir = data_dir
        self.memory_file = os.path.join(data_dir, "trade_memory.json")
        self.trades = []

        os.makedirs(data_dir, exist_ok=True)
        self._load()

        print("TradeMemory initialized (", len(self.trades), "trades)")


    def record(self, market, side, price, size, pnl, confidence):

        trade = {
            "timestamp": datetime.now(UTC).isoformat(),
            "market": market,
            "side": side,
            "price": price,
            "size": size,
            "pnl": pnl,
            "confidence": confidence,
            "won": pnl > 0
        }

        self.trades.append(trade)
        self._save()


    def get_avg_confidence_for_wins(self):

        wins = [t for t in self.trades if t["won"]]
        if not wins:
            return 0
        return sum(t["confidence"] for t in wins) / len(wins)


    def get_avg_confidence_for_losses(self):

        losses = [t for t in self.trades if not t["won"]]
        if not losses:
            return 0
        return sum(t["confidence"] for t in losses) / len(losses)


    def _load(self):

        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    self.trades = json.load(f)
            except:
                self.trades = []


    def _save(self):

        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.trades, f, indent=2)
        except:
            pass
