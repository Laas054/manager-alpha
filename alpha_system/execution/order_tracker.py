import json
import os
from datetime import datetime, UTC


class OrderTracker:
    """Suivi persistant de tous les ordres — open, filled, cancelled."""

    def __init__(self, data_dir="alpha_system/data"):

        os.makedirs(data_dir, exist_ok=True)
        self.file = os.path.join(data_dir, "orders.json")
        self.orders = {}

        self._load()
        print(f"OrderTracker initialized ({len(self.orders)} orders)")


    def track(self, order):
        """Enregistre un nouvel ordre."""

        order_id = order.get("order_id", order.get("id", "unknown"))
        order["tracked_at"] = datetime.now(UTC).isoformat()

        if "status" not in order:
            order["status"] = "OPEN"

        self.orders[order_id] = order
        self._save()


    def update_status(self, order_id, status, pnl=None):
        """Met à jour le statut d'un ordre."""

        if order_id in self.orders:
            self.orders[order_id]["status"] = status
            if pnl is not None:
                self.orders[order_id]["pnl"] = pnl
            self.orders[order_id]["updated_at"] = datetime.now(UTC).isoformat()
            self._save()


    def get_open_orders(self):
        """Retourne tous les ordres ouverts."""

        return [
            o for o in self.orders.values()
            if o["status"] == "OPEN"
        ]


    def get_all(self):
        return list(self.orders.values())


    def _save(self):

        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self.orders, f, indent=2)
        except Exception as e:
            print(f"  OrderTracker save error: {e}")


    def _load(self):

        if not os.path.exists(self.file):
            return

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                self.orders = json.load(f)
        except Exception:
            self.orders = {}
