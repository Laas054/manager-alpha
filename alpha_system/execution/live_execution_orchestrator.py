"""
Live Execution Orchestrator — pipeline d'exécution complet sécurisé.

Flux: guard -> wallet check -> execute -> wait fill -> open position -> audit

Connecte tous les modules d'exécution en un seul pipeline.
Compatible DRY et LIVE.
"""

from alpha_system.config import CONFIG


class LiveExecutionOrchestrator:
    """Orchestrateur d'exécution — pipeline complet guard -> wallet -> execute -> fill -> position."""

    def __init__(self, executor, position_manager, wallet_monitor,
                 guard, order_monitor=None, logger=None, database=None):

        self.executor = executor
        self.pm = position_manager
        self.wallet = wallet_monitor
        self.guard = guard
        self.order_monitor = order_monitor
        self.log = logger
        self.db = database

        # Stats
        self.total_signals = 0
        self.guard_blocked = 0
        self.wallet_blocked = 0
        self.executed = 0
        self.filled = 0
        self.failed = 0

        self._log("LiveExecutionOrchestrator initialized")

    # ============================================
    # EXECUTE (main pipeline)
    # ============================================

    def execute(self, signal):
        """Pipeline complet: guard -> wallet -> execute -> fill -> position."""

        self.total_signals += 1

        # 1. EXECUTION GUARD
        guard_ok, guard_reason = self.guard.validate(signal)
        if not guard_ok:
            self.guard_blocked += 1
            self._log(f"Guard blocked: {guard_reason}")
            return {"pnl": 0, "status": "GUARD_BLOCKED", "reason": guard_reason}

        # 2. WALLET CHECK
        wallet_ok, wallet_reason = self.wallet.validate_trade(signal.get("size", 0))
        if not wallet_ok:
            self.wallet_blocked += 1
            self._log(f"Wallet blocked: {wallet_reason}")
            return {"pnl": 0, "status": "WALLET_BLOCKED", "reason": wallet_reason}

        # 3. EXECUTE ORDER
        try:
            result = self.executor.execute(signal)
        except Exception as e:
            self.failed += 1
            self._log(f"Execution error: {e}")
            self._audit("EXECUTION_ERROR", str(e))
            return {"pnl": 0, "status": "FAILED", "reason": str(e)}

        if result is None or result.get("status") == "FAILED":
            self.failed += 1
            return result or {"pnl": 0, "status": "FAILED"}

        self.executed += 1

        # 4. WAIT FOR FILL (if order monitor available)
        if self.order_monitor and result.get("id"):
            fill_status = self.order_monitor.wait_for_fill(result["id"])
            if fill_status is None:
                self.failed += 1
                self._log(f"Order not filled — timeout")
                self._audit("ORDER_NOT_FILLED", f"id={result.get('id', '?')[:12]}")
                return {"pnl": 0, "status": "NOT_FILLED", "reason": "timeout"}
            self.filled += 1

        # 5. UPDATE WALLET BALANCE
        pnl = result.get("pnl", 0)
        self.wallet.update_balance(pnl)

        # 6. LOG
        self._log(
            f"EXECUTED | {signal.get('market', '?')[:40]} "
            f"| {signal.get('side')} @ {signal.get('price')} "
            f"| size:{signal.get('size')} | status:{result.get('status')}"
        )
        self._audit(
            "LIVE_EXECUTED",
            f"{signal.get('market', '?')[:40]} {result.get('status')}"
        )

        return result

    # ============================================
    # STATUS
    # ============================================

    def get_status(self):
        return {
            "total_signals": self.total_signals,
            "guard_blocked": self.guard_blocked,
            "wallet_blocked": self.wallet_blocked,
            "executed": self.executed,
            "filled": self.filled,
            "failed": self.failed,
            "guard": self.guard.get_status(),
            "wallet": self.wallet.get_status(),
        }

    def _log(self, msg):
        if self.log:
            self.log.info(f"[LIVE_EXEC] {msg}")

    def _audit(self, action, detail=""):
        if self.db:
            try:
                self.db.log_audit(action, detail)
            except Exception:
                pass
