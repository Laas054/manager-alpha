from datetime import datetime, UTC


class RiskEngineV2:
    """Risk Engine V2 — Protection complète du capital.
    check_drawdown(), check_loss_streak(), check_trade_limits(),
    add_position(), remove_position(), trailing stop."""

    def __init__(self, config):

        self.max_risk_per_trade = config["MAX_RISK_PER_TRADE"]
        self.max_drawdown = config["MAX_DRAWDOWN_PCT"]
        self.max_trade_size = config["MAX_TRADE_SIZE"]
        self.starting_capital = config["STARTING_CAPITAL"]

        # Limites (config-driven)
        self.max_daily_trades = config.get("MAX_TRADES_PER_DAY", 20)
        self.max_hourly_trades = config.get("MAX_TRADES_PER_HOUR", 5)
        self.max_daily_loss_pct = 0.05
        self.max_correlated_exposure = config.get("MAX_CORRELATED_EXPOSURE", 0.06)
        self.trailing_stop_pct = config.get("TRAILING_STOP_PCT", 0.05)

        # Loss streak
        self.max_loss_streak = config.get("MAX_LOSS_STREAK", 5)
        self.loss_streak = 0

        # Tracking journalier
        self.daily_trades = 0
        self.daily_pnl = 0
        self.last_reset_date = datetime.now(UTC).date()

        # Tracking horaire
        self.hourly_trades = 0
        self.last_hour = datetime.now(UTC).hour

        # Position tracking
        self.positions = {}  # market -> {"size": x, "entry_price": y, "peak_pnl": z}

        # Capital tracking pour trailing stop
        self.peak_capital = config["STARTING_CAPITAL"]

    # === VALIDATION PRINCIPALE ===

    def validate_trade(self, capital, size, confidence):
        """Valide un trade avant exécution. Retourne (ok, reason)."""

        self._check_daily_reset()
        self._check_hourly_reset()

        # 1. Capital positif
        if capital <= 0:
            return False, "no capital"

        # 2. Taille max
        if size > self.max_trade_size:
            return False, f"size {size} > max {self.max_trade_size}"

        # 3. Risque par trade
        risk_pct = size / capital
        if risk_pct > self.max_risk_per_trade:
            return False, f"risk {round(risk_pct*100,2)}% > max {self.max_risk_per_trade*100}%"

        # 4. Drawdown check
        dd_ok, dd_reason = self.check_drawdown(capital)
        if not dd_ok:
            return False, dd_reason

        # 5. Loss streak check
        ls_ok, ls_reason = self.check_loss_streak()
        if not ls_ok:
            return False, ls_reason

        # 6. Trade limits check
        tl_ok, tl_reason = self.check_trade_limits()
        if not tl_ok:
            return False, tl_reason

        # 7. Perte journalière
        daily_loss_pct = abs(min(0, self.daily_pnl)) / self.starting_capital
        if daily_loss_pct > self.max_daily_loss_pct:
            return False, f"daily loss {round(daily_loss_pct*100,2)}% > max {self.max_daily_loss_pct*100}%"

        # 8. Confidence minimum
        if confidence < 0.65:
            return False, f"confidence {confidence} < 0.65"

        # 9. Trailing stop
        ts_ok, ts_reason = self._check_trailing_stop(capital)
        if not ts_ok:
            return False, ts_reason

        # 10. Correlated exposure
        total_exposure = sum(p["size"] for p in self.positions.values())
        if self.starting_capital > 0:
            exposure_pct = (total_exposure + size) / self.starting_capital
            if exposure_pct > self.max_correlated_exposure:
                return False, f"exposure {round(exposure_pct*100,2)}% > max {self.max_correlated_exposure*100}%"

        return True, f"OK risk:{round(risk_pct*100,2)}%"

    # === CHECK METHODS (directive obligatoire) ===

    def check_drawdown(self, capital):
        """Vérifie le drawdown global. Retourne (ok, reason)."""

        if self.starting_capital <= 0:
            return True, "no starting capital"

        drawdown = (self.starting_capital - capital) / self.starting_capital

        if drawdown > self.max_drawdown:
            return False, f"drawdown {round(drawdown*100,2)}% > max {self.max_drawdown*100}%"

        return True, f"drawdown {round(drawdown*100,2)}% OK"

    def check_loss_streak(self):
        """Vérifie la série de pertes. Retourne (ok, reason)."""

        if self.loss_streak >= self.max_loss_streak:
            return False, f"loss streak {self.loss_streak} >= max {self.max_loss_streak}"

        return True, f"streak {self.loss_streak} OK"

    def check_trade_limits(self):
        """Vérifie les limites de trades (jour + heure). Retourne (ok, reason)."""

        self._check_daily_reset()
        self._check_hourly_reset()

        if self.daily_trades >= self.max_daily_trades:
            return False, f"daily trades {self.daily_trades} >= max {self.max_daily_trades}"

        if self.hourly_trades >= self.max_hourly_trades:
            return False, f"hourly trades {self.hourly_trades} >= max {self.max_hourly_trades}"

        return True, f"daily:{self.daily_trades}/{self.max_daily_trades} hourly:{self.hourly_trades}/{self.max_hourly_trades}"

    # === POSITION TRACKING (directive obligatoire) ===

    def add_position(self, market, size, entry_price=0):
        """Ajoute une position ouverte au tracking."""

        self.positions[market] = {
            "size": size,
            "entry_price": entry_price,
            "peak_pnl": 0,
            "opened_at": datetime.now(UTC).isoformat(),
        }

    def remove_position(self, market):
        """Retire une position fermée du tracking."""

        if market in self.positions:
            del self.positions[market]

    def get_positions(self):
        """Retourne toutes les positions ouvertes."""

        return dict(self.positions)

    # === RECORD ===

    def record_trade(self, pnl):
        """Enregistre le résultat d'un trade."""

        self.daily_trades += 1
        self.hourly_trades += 1
        self.daily_pnl += pnl

        if pnl < 0:
            self.loss_streak += 1
        else:
            self.loss_streak = 0

    def update_capital(self, capital):
        """Met à jour le peak capital pour le trailing stop."""

        if capital > self.peak_capital:
            self.peak_capital = capital

    # === INTERNAL ===

    def _check_trailing_stop(self, capital):
        """Trailing stop — bloque si le capital a chuté depuis le peak."""

        self.update_capital(capital)

        if self.peak_capital <= 0:
            return True, "no peak"

        drop = (self.peak_capital - capital) / self.peak_capital

        if drop > self.trailing_stop_pct:
            return False, f"trailing stop: -{round(drop*100,2)}% from peak {round(self.peak_capital,2)}"

        return True, f"trailing OK (-{round(drop*100,2)}%)"

    def _check_daily_reset(self):
        """Reset automatique des compteurs journaliers."""

        today = datetime.now(UTC).date()
        if today != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0
            self.loss_streak = 0
            self.last_reset_date = today

    def _check_hourly_reset(self):
        """Reset automatique des compteurs horaires."""

        current_hour = datetime.now(UTC).hour
        if current_hour != self.last_hour:
            self.hourly_trades = 0
            self.last_hour = current_hour

    def get_status(self):

        return {
            "loss_streak": self.loss_streak,
            "daily_trades": self.daily_trades,
            "hourly_trades": self.hourly_trades,
            "daily_pnl": round(self.daily_pnl, 2),
            "peak_capital": round(self.peak_capital, 2),
            "open_positions": len(self.positions),
            "total_exposure": round(sum(p["size"] for p in self.positions.values()), 2),
        }
