import json
import os


class PerformanceAnalyzer:

    def __init__(self, data_dir="alpha_system/data"):
        self.file = os.path.join(data_dir, "trades.json")

    def analyze(self):

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                trades = json.load(f)
        except Exception:
            return None

        if not trades:
            return None

        pnl = sum(t.get("pnl", 0) for t in trades)
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        total = len(trades)
        winrate = round(wins / total * 100, 1) if total > 0 else 0

        return {
            "total_trades": total,
            "total_pnl": round(pnl, 2),
            "wins": wins,
            "losses": total - wins,
            "winrate": winrate
        }
