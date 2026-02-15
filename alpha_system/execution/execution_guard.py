"""
Execution Safety Guard — dernière ligne de défense avant envoi d'ordre.

Valide tous les paramètres critiques de l'ordre.
Bloque les trades dangereux avant qu'ils n'atteignent le CLOB.
"""

from alpha_system.config import CONFIG


class ExecutionGuard:
    """Garde de sécurité — valide chaque ordre avant soumission."""

    def __init__(self, config=None, logger=None, database=None):

        cfg = config or CONFIG
        self.max_size = cfg.get("MAX_TRADE_SIZE", 100)
        self.max_risk_pct = cfg.get("MAX_RISK_PER_TRADE", 0.02)
        self.log = logger
        self.db = database

        # Stats
        self.validated = 0
        self.blocked = 0

        self._log("ExecutionGuard initialized")

    # ============================================
    # VALIDATE ORDER
    # ============================================

    def validate(self, order):
        """Valide un ordre avant soumission. Retourne (ok, reason)."""

        self.validated += 1

        # Size
        size = order.get("size", 0)
        if size <= 0:
            return self._block(f"invalid size: {size}")
        if size > self.max_size:
            return self._block(f"size {size} > max {self.max_size}")

        # Price
        price = order.get("price", 0)
        if price <= 0 or price >= 1:
            return self._block(f"invalid price: {price}")

        # Side
        side = order.get("side", "")
        if not side:
            return self._block("missing side")

        # Token ID (requis en LIVE)
        if CONFIG.get("MODE") == "LIVE" and not order.get("token_id"):
            return self._block("token_id required for LIVE")

        # Market name
        if not order.get("market"):
            return self._block("missing market name")

        return True, "OK"

    def _block(self, reason):
        """Bloque un ordre et log."""

        self.blocked += 1
        self._log(f"BLOCKED: {reason}")
        self._audit("GUARD_BLOCKED", reason)
        return False, reason

    # ============================================
    # STATUS
    # ============================================

    def get_status(self):
        return {
            "validated": self.validated,
            "blocked": self.blocked,
            "block_rate": round(
                self.blocked / max(1, self.validated) * 100, 1
            ),
        }

    def _log(self, msg):
        if self.log:
            self.log.info(f"[GUARD] {msg}")

    def _audit(self, action, detail=""):
        if self.db:
            try:
                self.db.log_audit(action, detail)
            except Exception:
                pass
