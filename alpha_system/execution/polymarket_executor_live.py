"""
Polymarket Executor LIVE — Exécution réelle professionnelle.

Sécurité maximale :
- Validation complète avant envoi
- Limit orders uniquement
- Retry automatique avec backoff
- Order tracking (pending, filled, failed)
- Audit log complet
- Intégration PositionManager

Compatible avec ExecutionEngine.execute(decision) interface.
"""

import os
import uuid
import time
import traceback
from datetime import datetime, UTC


class PolymarketExecutorLive:
    """Executor LIVE Polymarket — ordres réels signés sur Polygon."""

    def __init__(self, position_manager=None, logger=None, database=None):

        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY", "")
        self.pm = position_manager
        self.log = logger
        self.db = database
        self.client = None

        # Order tracking
        self.pending_orders = {}
        self.filled_orders = []
        self.failed_orders = []

        # Stats
        self.total_submitted = 0
        self.total_filled = 0
        self.total_failed = 0

        # Config
        self.max_retries = 2
        self.retry_delay = 2

        # Init CLOB client
        if not self.private_key or self.private_key == "your_private_key_here":
            self._log("WARNING: No valid POLYMARKET_PRIVATE_KEY — LIVE trading disabled")
            return

        try:
            from py_clob_client.client import ClobClient

            self.client = ClobClient(
                "https://clob.polymarket.com",
                key=self.private_key,
                chain_id=137,  # Polygon
            )
            self._log("PolymarketExecutorLive initialized — CLOB client ready")
            self._audit("EXECUTOR_INIT", "LIVE mode — CLOB client connected")
        except ImportError:
            self._log("ERROR: py-clob-client not installed. Run: pip install py-clob-client")
            self._audit("EXECUTOR_INIT_FAILED", "py-clob-client missing")
        except Exception as e:
            self._log(f"ERROR: CLOB client init failed: {e}")
            self._audit("EXECUTOR_INIT_FAILED", str(e))

    # ============================================
    # EXECUTE (main entry — compatible interface)
    # ============================================

    def execute(self, decision):
        """Exécute un trade LIVE. Compatible avec ExecutionEngine interface."""

        # 1. Validate decision
        valid, reason = self._validate_decision(decision)
        if not valid:
            self._log(f"REJECTED: {reason}")
            self._audit("ORDER_REJECTED", reason)
            return {"pnl": 0, "status": "REJECTED", "reason": reason}

        # 2. Check client
        if not self.client:
            self._log("ERROR: No CLOB client — cannot execute LIVE")
            return {"pnl": 0, "status": "FAILED", "reason": "no_client"}

        # 3. Build order
        order = self._build_order(decision)

        # 4. Submit with retry
        result = self._submit_with_retry(order, decision)

        # 5. Track result
        if result and result.get("status") == "LIVE":
            self.total_filled += 1
            self.filled_orders.append(result)

            # Open position in PositionManager
            if self.pm:
                self.pm.open_position(
                    market_id=decision["market"],
                    token_id=decision.get("token_id", ""),
                    side=decision["side"],
                    entry_price=decision["price"],
                    size=decision.get("size", 1),
                    confidence=decision.get("confidence", 0),
                    model=decision.get("model", ""),
                )
        else:
            self.total_failed += 1
            self.failed_orders.append({
                "order": order,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return result

    # ============================================
    # CLOSE POSITION
    # ============================================

    def close_position(self, market_id, current_price, size, side, token_id):
        """Ferme une position ouverte — envoie l'ordre inverse."""

        if not self.client:
            self._log("ERROR: No CLOB client for close")
            return None

        # Côté inverse
        close_side = "NO" if side in ("YES", "BUY", "buy") else "YES"

        close_decision = {
            "market": market_id,
            "token_id": token_id,
            "side": close_side,
            "price": current_price,
            "size": size,
        }

        self._log(f"Closing position: {market_id[:40]} {close_side} @ {current_price}")
        self._audit("POSITION_CLOSE_ORDER", f"{market_id[:40]} {close_side} size={size}")

        return self.execute(close_decision)

    # ============================================
    # BUILD ORDER
    # ============================================

    def _build_order(self, decision):
        """Construit l'ordre avec tous les paramètres."""

        order_id = str(uuid.uuid4())

        return {
            "id": order_id,
            "token_id": decision.get("token_id"),
            "side": decision["side"],
            "price": decision["price"],
            "size": decision.get("size", 1),
            "type": "limit",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # ============================================
    # SUBMIT WITH RETRY
    # ============================================

    def _submit_with_retry(self, order, decision):
        """Soumet l'ordre avec retry automatique."""

        self.total_submitted += 1

        for attempt in range(self.max_retries + 1):
            try:
                result = self._submit_order(order)

                if result:
                    self._log(
                        f"[LIVE] Order FILLED | {decision['market'][:40]} "
                        f"| {order['side']} @ {order['price']} size:{order['size']}"
                    )
                    self._audit(
                        "ORDER_FILLED",
                        f"{decision['market'][:40]} {order['side']} "
                        f"@ {order['price']} size={order['size']}"
                    )

                    return {
                        "id": order["id"],
                        "pnl": 0,  # PnL calculé à la fermeture
                        "status": "LIVE",
                        "result": result,
                        "order": order,
                    }

                if attempt < self.max_retries:
                    self._log(f"Retry {attempt + 1}/{self.max_retries}...")
                    time.sleep(self.retry_delay * (attempt + 1))

            except Exception as e:
                self._log(f"Submit error (attempt {attempt + 1}): {e}")
                self._audit("ORDER_ERROR", f"attempt={attempt + 1} error={e}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))

        # All retries failed
        self._log(f"ORDER FAILED after {self.max_retries + 1} attempts")
        self._audit("ORDER_FAILED", f"id={order['id']} all retries exhausted")

        return {"pnl": 0, "status": "FAILED", "reason": "all_retries_failed"}

    def _submit_order(self, order):
        """Soumet un seul ordre au CLOB Polymarket."""

        from py_clob_client.clob_types import OrderArgs

        token_id = order["token_id"]

        order_args = OrderArgs(
            price=order["price"],
            size=order["size"],
            side=order["side"],
            token_id=token_id,
        )

        # Sign
        signed_order = self.client.create_order(order_args)

        # Send
        result = self.client.post_order(signed_order)

        self.pending_orders[order["id"]] = {
            "order": order,
            "result": result,
            "submitted_at": datetime.now(UTC).isoformat(),
        }

        return result

    # ============================================
    # VALIDATION
    # ============================================

    def _validate_decision(self, decision):
        """Valide la décision avant envoi."""

        if not decision:
            return False, "empty decision"

        if not decision.get("token_id"):
            return False, "token_id required for LIVE execution"

        if not decision.get("side"):
            return False, "side required"

        price = decision.get("price", 0)
        if price <= 0 or price >= 1:
            return False, f"invalid price: {price}"

        size = decision.get("size", 0)
        if size <= 0:
            return False, f"invalid size: {size}"

        if size > 1000:
            return False, f"size too large: {size} (max 1000)"

        return True, "OK"

    # ============================================
    # LOGGING / AUDIT
    # ============================================

    def _log(self, msg):
        if self.log:
            self.log.info(f"[EXECUTOR] {msg}")
        else:
            print(f"  [EXECUTOR] {msg}")

    def _audit(self, action, detail=""):
        if self.db:
            try:
                self.db.log_audit(action, detail)
            except Exception:
                pass

    # ============================================
    # STATUS
    # ============================================

    def get_status(self):
        return {
            "client_ready": self.client is not None,
            "total_submitted": self.total_submitted,
            "total_filled": self.total_filled,
            "total_failed": self.total_failed,
            "pending_count": len(self.pending_orders),
            "fill_rate": round(
                self.total_filled / max(1, self.total_submitted) * 100, 1
            ),
        }
