"""
Position Manager institutionnel — gestion complète des positions.

Ouverture, suivi temps réel, take profit, stop loss,
trailing stop, fermeture automatique, PnL, sync RiskEngine.
"""

import time
from datetime import datetime, UTC


# ============================================
# POSITION
# ============================================

class Position:
    """Représente une position ouverte."""

    def __init__(
        self,
        market_id,
        token_id,
        side,
        entry_price,
        size,
        confidence=0,
        model="",
        take_profit=None,
        stop_loss=None,
        trailing_stop=None,
    ):
        self.market_id = market_id
        self.token_id = token_id
        self.side = side
        self.entry_price = entry_price
        self.size = size
        self.confidence = confidence
        self.model = model

        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop

        self.highest_price = entry_price
        self.lowest_price = entry_price
        self.current_price = entry_price

        self.status = "OPEN"
        self.open_time = datetime.now(UTC)
        self.close_time = None
        self.exit_price = None
        self.exit_reason = None
        self.pnl = 0

    def to_dict(self):
        return {
            "market_id": self.market_id,
            "token_id": self.token_id,
            "side": self.side,
            "entry_price": self.entry_price,
            "size": self.size,
            "confidence": self.confidence,
            "status": self.status,
            "pnl": round(self.pnl, 4),
            "highest_price": self.highest_price,
            "lowest_price": self.lowest_price,
            "open_time": self.open_time.isoformat(),
        }


# ============================================
# POSITION MANAGER
# ============================================

class PositionManager:
    """Gestion complète des positions — TP, SL, trailing, sync risk."""

    def __init__(self, execution=None, risk_engine=None, database=None,
                 cost_calc=None, logger=None):

        self.execution = execution
        self.risk_engine = risk_engine
        self.database = database
        self.cost_calc = cost_calc
        self.log = logger

        self.positions = {}
        self.closed_positions = []

        # Defaults
        self.default_tp_pct = 0.10
        self.default_sl_pct = 0.05
        self.default_trailing_pct = 0.05

        if self.log:
            self.log.info("Position Manager initialized")

    # ============================================
    # OPEN POSITION
    # ============================================

    def open_position(
        self,
        market_id,
        token_id,
        side,
        entry_price,
        size,
        confidence=0,
        model="",
        take_profit_pct=None,
        stop_loss_pct=None,
        trailing_stop_pct=None,
    ):
        """Ouvre une nouvelle position avec TP/SL/trailing automatiques."""

        tp_pct = take_profit_pct if take_profit_pct is not None else self.default_tp_pct
        sl_pct = stop_loss_pct if stop_loss_pct is not None else self.default_sl_pct
        trail_pct = trailing_stop_pct if trailing_stop_pct is not None else self.default_trailing_pct

        # Calculer les niveaux TP/SL selon le side
        # YES/BUY = on gagne si le prix monte
        # NO/SELL = on gagne si le prix baisse
        if side in ("YES", "BUY", "buy"):
            take_profit = entry_price * (1 + tp_pct)
            stop_loss = entry_price * (1 - sl_pct)
        else:
            take_profit = entry_price * (1 - tp_pct)
            stop_loss = entry_price * (1 + sl_pct)

        position = Position(
            market_id=market_id,
            token_id=token_id,
            side=side,
            entry_price=entry_price,
            size=size,
            confidence=confidence,
            model=model,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_stop=trail_pct,
        )

        self.positions[market_id] = position

        # Sync avec RiskEngine
        if self.risk_engine:
            self.risk_engine.add_position(market_id, size, entry_price)

        if self.log:
            self.log.info(
                f"POSITION OPEN | {market_id[:50]} | {side} @ {entry_price} "
                f"| size:{size} | TP:{round(take_profit, 4)} SL:{round(stop_loss, 4)}"
            )

        if self.database:
            self.database.log_audit(
                "POSITION_OPEN",
                f"{market_id[:50]} {side} @ {entry_price} size={size}"
            )

        return position

    # ============================================
    # UPDATE PRICE
    # ============================================

    def update_price(self, market_id, current_price):
        """Met à jour le prix et vérifie les conditions de sortie."""

        if market_id not in self.positions:
            return None

        position = self.positions[market_id]

        if position.status != "OPEN":
            return None

        position.current_price = current_price

        # Update highest / lowest
        if current_price > position.highest_price:
            position.highest_price = current_price
        if current_price < position.lowest_price:
            position.lowest_price = current_price

        # Calculate PnL
        position.pnl = self._calculate_pnl(position, current_price)

        # Check exit conditions (priority: TP > SL > Trailing)
        if self._should_take_profit(position, current_price):
            return self.close_position(market_id, current_price, "TAKE_PROFIT")

        if self._should_stop_loss(position, current_price):
            return self.close_position(market_id, current_price, "STOP_LOSS")

        if self._should_trailing_stop(position, current_price):
            return self.close_position(market_id, current_price, "TRAILING_STOP")

        return None

    def update_all_prices(self, price_map):
        """Met à jour les prix de toutes les positions ouvertes.
        price_map: {market_id: current_price}"""

        results = []
        for market_id, price in price_map.items():
            result = self.update_price(market_id, price)
            if result:
                results.append(result)
        return results

    # ============================================
    # EXIT CONDITIONS
    # ============================================

    def _should_take_profit(self, position, price):

        if position.take_profit is None:
            return False

        if position.side in ("YES", "BUY", "buy"):
            return price >= position.take_profit
        else:
            return price <= position.take_profit

    def _should_stop_loss(self, position, price):

        if position.stop_loss is None:
            return False

        if position.side in ("YES", "BUY", "buy"):
            return price <= position.stop_loss
        else:
            return price >= position.stop_loss

    def _should_trailing_stop(self, position, price):

        if position.trailing_stop is None or position.trailing_stop <= 0:
            return False

        pct = position.trailing_stop

        if position.side in ("YES", "BUY", "buy"):
            trailing_price = position.highest_price * (1 - pct)
            return price <= trailing_price and position.highest_price > position.entry_price
        else:
            trailing_price = position.lowest_price * (1 + pct)
            return price >= trailing_price and position.lowest_price < position.entry_price

    # ============================================
    # CLOSE POSITION
    # ============================================

    def close_position(self, market_id, exit_price, reason="MANUAL"):
        """Ferme une position et enregistre le résultat."""

        if market_id not in self.positions:
            return None

        position = self.positions[market_id]

        if position.status != "OPEN":
            return None

        position.status = "CLOSED"
        position.close_time = datetime.now(UTC)
        position.exit_price = exit_price
        position.exit_reason = reason
        position.pnl = self._calculate_pnl(position, exit_price)

        # Ajuster PnL avec les frais
        adjusted_pnl = position.pnl
        if self.cost_calc:
            cost_result = self.cost_calc.adjust_pnl(position.pnl, position.size, exit_price)
            adjusted_pnl = cost_result["adjusted_pnl"]

        if self.log:
            self.log.info(
                f"POSITION CLOSED | {market_id[:50]} | {reason} "
                f"| entry:{position.entry_price} exit:{exit_price} "
                f"| PnL:{round(adjusted_pnl, 4)}"
            )

        # Record in database
        if self.database:
            self.database.record_trade(
                market=market_id,
                side=position.side,
                price=position.entry_price,
                size=position.size,
                pnl=adjusted_pnl,
                confidence=position.confidence,
                model=position.model,
                source="position_manager",
                status=f"CLOSED_{reason}",
            )
            self.database.log_audit(
                "POSITION_CLOSE",
                f"{market_id[:50]} {reason} pnl={round(adjusted_pnl, 4)}"
            )

        # Sync avec RiskEngine
        if self.risk_engine:
            self.risk_engine.remove_position(market_id)
            self.risk_engine.record_trade(adjusted_pnl)

        # Move to closed
        self.closed_positions.append(position)
        del self.positions[market_id]

        return {
            "market_id": market_id,
            "reason": reason,
            "pnl": round(adjusted_pnl, 4),
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "side": position.side,
            "size": position.size,
        }

    def close_all(self, current_prices, reason="SHUTDOWN"):
        """Ferme toutes les positions ouvertes."""

        results = []
        market_ids = list(self.positions.keys())

        for market_id in market_ids:
            price = current_prices.get(market_id, self.positions[market_id].current_price)
            result = self.close_position(market_id, price, reason)
            if result:
                results.append(result)

        return results

    # ============================================
    # PNL CALCULATION
    # ============================================

    def _calculate_pnl(self, position, current_price):
        """Calcule le PnL brut d'une position."""

        if position.side in ("YES", "BUY", "buy"):
            return round((current_price - position.entry_price) * position.size, 4)
        else:
            return round((position.entry_price - current_price) * position.size, 4)

    # ============================================
    # QUERIES
    # ============================================

    def get_open_positions(self):
        """Retourne les positions ouvertes."""

        return {k: v for k, v in self.positions.items() if v.status == "OPEN"}

    def get_position(self, market_id):
        """Retourne une position spécifique."""

        return self.positions.get(market_id)

    def has_position(self, market_id):
        """Vérifie si une position est ouverte sur ce marché."""

        return market_id in self.positions and self.positions[market_id].status == "OPEN"

    def get_total_exposure(self):
        """Retourne l'exposition totale des positions ouvertes."""

        return round(sum(p.size for p in self.positions.values() if p.status == "OPEN"), 4)

    def get_total_unrealized_pnl(self):
        """Retourne le PnL non-réalisé total."""

        return round(sum(p.pnl for p in self.positions.values() if p.status == "OPEN"), 4)

    def get_status(self):
        """Retourne le statut complet du position manager."""

        open_pos = self.get_open_positions()
        total_pnl_closed = sum(p.pnl for p in self.closed_positions)

        return {
            "open_count": len(open_pos),
            "closed_count": len(self.closed_positions),
            "total_exposure": self.get_total_exposure(),
            "unrealized_pnl": self.get_total_unrealized_pnl(),
            "realized_pnl": round(total_pnl_closed, 4),
            "positions": [p.to_dict() for p in open_pos.values()],
        }
