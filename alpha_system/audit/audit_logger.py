import json
import os
import logging
from datetime import datetime, UTC


class AuditLogger:
    """Journal d'audit institutionnel — fichier JSONL + logging Python."""

    def __init__(self, data_dir="alpha_system/data"):

        os.makedirs(data_dir, exist_ok=True)
        self.file = os.path.join(data_dir, "audit_log.jsonl")

        # Logging Python vers fichier
        self.logger = logging.getLogger("alpha_audit")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler(
                os.path.join(data_dir, "audit.log"),
                encoding="utf-8"
            )
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            ))
            self.logger.addHandler(handler)

        print("AuditLogger initialized")


    def log(self, action, market="", detail=""):
        """Log une action dans les deux systèmes."""

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "market": market,
            "detail": detail
        }

        # JSONL persistant
        try:
            with open(self.file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        # Logging Python
        msg = f"{action} | {market} | {detail}"
        self.logger.info(msg)

        print(f"  [AUDIT] {action}: {market} \u2014 {detail}")
