import json
import os
from datetime import datetime, UTC


class AuditLogger:

    def __init__(self, log_dir="alpha_system/data"):

        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "audit_log.jsonl")
        self.entries = []

        os.makedirs(log_dir, exist_ok=True)

        print("AuditLogger initialized")


    def log(self, action, market, detail=""):

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "market": market,
            "detail": detail
        }

        self.entries.append(entry)

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except:
            pass

        print(f"  [AUDIT] {action}: {market} — {detail}")


    def get_entries(self, limit=50):

        return self.entries[-limit:]
