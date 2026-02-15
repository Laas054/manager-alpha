import json
import os
from datetime import datetime, UTC


class DecisionLogger:
    """Log de toutes les décisions AI pour analyse."""

    def __init__(self, data_dir="alpha_system/data"):

        self.file = os.path.join(data_dir, "decisions.jsonl")
        os.makedirs(data_dir, exist_ok=True)

        print("DecisionLogger initialized")


    def log(self, decision, executed=False, blocked_reason=""):

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "market": decision.get("market", ""),
            "side": decision.get("side", ""),
            "price": decision.get("price", 0),
            "size": decision.get("size", 0),
            "confidence": decision.get("confidence", 0),
            "model": decision.get("model", ""),
            "executed": executed,
            "blocked_reason": blocked_reason
        }

        try:
            with open(self.file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except:
            pass
