import json
import os
from datetime import datetime, UTC


class PositionSync:
    """Synchronise les positions locales avec Polymarket (LIVE mode)."""

    def __init__(self, client=None, data_dir="alpha_system/data"):

        self.client = client
        os.makedirs(data_dir, exist_ok=True)
        self.file = os.path.join(data_dir, "positions.json")

        print("PositionSync initialized")


    def sync(self):
        """Récupère les positions réelles depuis Polymarket."""

        if not self.client:
            return self._load_local()

        try:
            positions = self.client.get_positions()
            self._save_local(positions)
            return positions
        except Exception as e:
            print(f"  PositionSync error: {e}")
            return self._load_local()


    def save_positions(self, exposure_engine):
        """Sauvegarde les positions locales depuis ExposureEngine."""

        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "available": exposure_engine.available,
            "positions": exposure_engine.positions,
        }

        self._save_local(data)


    def restore_positions(self, exposure_engine):
        """Restaure les positions locales dans ExposureEngine."""

        data = self._load_local()
        if not data:
            return False

        exposure_engine.available = data.get("available", exposure_engine.available)
        exposure_engine.positions = data.get("positions", {})

        print(f"  Positions restored | {len(exposure_engine.positions)} open | Available: {round(exposure_engine.available, 2)}")
        return True


    def _save_local(self, data):

        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"  PositionSync save error: {e}")


    def _load_local(self):

        if not os.path.exists(self.file):
            return None

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
