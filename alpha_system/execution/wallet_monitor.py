"""
Wallet Balance Monitor — empêche les trades si balance insuffisante.

Vérifie la balance wallet Polygon avant chaque trade LIVE.
Cache la balance pour éviter les appels réseau répétés.
Compatible DRY (balance simulée) et LIVE (balance réelle).
"""

import time
from alpha_system.config import CONFIG


class WalletMonitor:
    """Monitor balance wallet — bloque si fonds insuffisants."""

    def __init__(self, polymarket_client=None, logger=None, database=None):

        self.client = polymarket_client
        self.log = logger
        self.db = database

        self.cached_balance = 0
        self.last_check = 0
        self.cache_ttl = 30  # Refresh balance toutes les 30s
        self.mode = CONFIG.get("MODE", "DRY")

        # Stats
        self.checks_total = 0
        self.checks_blocked = 0

        # En DRY mode, simuler la balance depuis le capital config
        if self.mode != "LIVE" or not self.client:
            self.cached_balance = CONFIG.get("STARTING_CAPITAL", 1000)

        self._log("WalletMonitor initialized")

    # ============================================
    # GET BALANCE
    # ============================================

    def get_balance(self):
        """Retourne la balance actuelle du wallet."""

        now = time.time()

        # Cache valide ?
        if now - self.last_check < self.cache_ttl and self.cached_balance > 0:
            return self.cached_balance

        # DRY mode — pas d'appel réseau
        if self.mode != "LIVE" or not self.client:
            return self.cached_balance

        # LIVE — query balance réelle
        try:
            balance = self.client.get_balance()
            self.cached_balance = float(balance)
            self.last_check = now
            self._log(f"Balance updated: {self.cached_balance}")
        except Exception as e:
            self._log(f"Balance check failed: {e} — using cached: {self.cached_balance}")

        return self.cached_balance

    def refresh_balance(self):
        """Force un refresh de la balance."""

        self.last_check = 0
        return self.get_balance()

    # ============================================
    # VALIDATE TRADE
    # ============================================

    def validate_trade(self, size):
        """Vérifie que la balance est suffisante pour le trade."""

        self.checks_total += 1

        balance = self.get_balance()

        if size > balance:
            self.checks_blocked += 1
            reason = f"Insufficient balance: need {size}, have {balance}"
            self._log(f"BLOCKED: {reason}")
            self._audit("WALLET_BLOCKED", reason)
            return False, reason

        if size > balance * 0.5:
            self._log(f"WARNING: Trade uses {round(size/balance*100, 1)}% of balance")

        return True, f"OK (balance: {round(balance, 2)})"

    # ============================================
    # UPDATE BALANCE (after trade)
    # ============================================

    def update_balance(self, pnl):
        """Met à jour la balance après un trade (DRY mode)."""

        self.cached_balance += pnl
        self.cached_balance = max(0, self.cached_balance)

    # ============================================
    # STATUS
    # ============================================

    def get_status(self):
        return {
            "balance": round(self.cached_balance, 2),
            "mode": self.mode,
            "checks_total": self.checks_total,
            "checks_blocked": self.checks_blocked,
        }

    def _log(self, msg):
        if self.log:
            self.log.info(f"[WALLET] {msg}")

    def _audit(self, action, detail=""):
        if self.db:
            try:
                self.db.log_audit(action, detail)
            except Exception:
                pass
