"""
Order Fill Monitor — vérifie si un ordre est réellement exécuté.

Poll le statut de l'ordre jusqu'à fill ou timeout.
Compatible DRY (fill instantané) et LIVE (poll CLOB).
"""

import time
from datetime import datetime, UTC

from alpha_system.config import CONFIG


class OrderMonitor:
    """Monitor les ordres en attente — confirme les fills."""

    def __init__(self, polymarket_client=None, logger=None, database=None):

        self.client = polymarket_client
        self.log = logger
        self.db = database
        self.mode = CONFIG.get("MODE", "DRY")

        # Tracking
        self.monitored_orders = {}
        self.filled_count = 0
        self.timeout_count = 0
        self.error_count = 0

        self._log("OrderMonitor initialized")

    # ============================================
    # WAIT FOR FILL
    # ============================================

    def wait_for_fill(self, order_id, timeout=30, poll_interval=1):
        """Attend qu'un ordre soit rempli. Retourne le statut ou None."""

        # DRY mode — fill instantané
        if self.mode != "LIVE" or not self.client:
            self.filled_count += 1
            return {
                "order_id": order_id,
                "status": "filled",
                "filled_at": datetime.now(UTC).isoformat(),
                "mode": "DRY",
            }

        # LIVE — poll le statut
        self._log(f"Monitoring order {order_id[:12]}... (timeout: {timeout}s)")
        self.monitored_orders[order_id] = {
            "start": time.time(),
            "status": "pending",
        }

        start = time.time()

        while time.time() - start < timeout:
            try:
                status = self.client.get_order(order_id)

                if status is None:
                    time.sleep(poll_interval)
                    continue

                order_status = status.get("status", "").lower()

                if order_status == "filled" or order_status == "matched":
                    self.filled_count += 1
                    self.monitored_orders[order_id]["status"] = "filled"
                    self._log(f"Order {order_id[:12]} FILLED")
                    self._audit("ORDER_FILLED", f"id={order_id[:12]}")
                    return status

                if order_status in ("cancelled", "canceled", "expired"):
                    self.monitored_orders[order_id]["status"] = order_status
                    self._log(f"Order {order_id[:12]} {order_status.upper()}")
                    self._audit("ORDER_CANCELLED", f"id={order_id[:12]} status={order_status}")
                    return status

                time.sleep(poll_interval)

            except Exception as e:
                self.error_count += 1
                self._log(f"Poll error: {e}")
                time.sleep(poll_interval)

        # Timeout
        self.timeout_count += 1
        self.monitored_orders[order_id]["status"] = "timeout"
        self._log(f"Order {order_id[:12]} TIMEOUT after {timeout}s")
        self._audit("ORDER_TIMEOUT", f"id={order_id[:12]} timeout={timeout}s")

        return None

    # ============================================
    # CHECK ORDER STATUS (non-blocking)
    # ============================================

    def check_order(self, order_id):
        """Vérifie le statut d'un ordre sans bloquer."""

        if self.mode != "LIVE" or not self.client:
            return {"order_id": order_id, "status": "filled", "mode": "DRY"}

        try:
            return self.client.get_order(order_id)
        except Exception as e:
            self._log(f"Check error: {e}")
            return None

    # ============================================
    # STATUS
    # ============================================

    def get_status(self):
        return {
            "filled": self.filled_count,
            "timeouts": self.timeout_count,
            "errors": self.error_count,
            "monitoring": len([o for o in self.monitored_orders.values()
                              if o["status"] == "pending"]),
        }

    def _log(self, msg):
        if self.log:
            self.log.info(f"[ORDER_MONITOR] {msg}")

    def _audit(self, action, detail=""):
        if self.db:
            try:
                self.db.log_audit(action, detail)
            except Exception:
                pass
