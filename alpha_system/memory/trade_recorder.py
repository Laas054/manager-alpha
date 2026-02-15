import json
import os
from datetime import datetime, UTC


class TradeRecorder:

    def __init__(self, data_dir="alpha_system/data"):
        os.makedirs(data_dir, exist_ok=True)
        self.file = os.path.join(data_dir, "trades.json")

    def record(self, trade):

        data = self._load()

        trade["timestamp"] = datetime.now(UTC).isoformat()
        data.append(trade)

        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"  TradeRecorder error: {e}")

    def get_all(self):
        return self._load()

    def _load(self):

        if not os.path.exists(self.file):
            return []

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
