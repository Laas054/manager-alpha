from datetime import datetime, UTC


class RiskEngineV2:
    """Risk Engine V2 — Protection complète du capital."""

    def __init__(self, config):

        self.max_risk_per_trade = config["MAX_RISK_PER_TRADE"]
        self.max_drawdown = config["MAX_DRAWDOWN_PCT"]
        self.max_trade_size = config["MAX_TRADE_SIZE"]
        self.starting_capital = config["STARTING_CAPITAL"]

        # Limites journalières
        self.max_daily_trades = 50
        self.max_daily_loss_pct = 0.05

        # Loss streak
        self.max_loss_streak = 5
        self.loss_streak = 0

        # Tracking journalier
        self.daily_trades = 0
        self.daily_pnl = 0
        self.last_reset_date = datetime.now(UTC).date()

    def validate_trade(self, capital, size, confidence):
        """Valide un trade avant exécution. Retourne (ok, reason)."""

        self._check_daily_reset()

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

        # 4. Drawdown global
        drawdown = (self.starting_capital - capital) / self.starting_capital
        if drawdown > self.max_drawdown:
            return False, f"drawdown {round(drawdown*100,2)}% > max {self.max_drawdown*100}%"

        # 5. Loss streak
        if self.loss_streak >= self.max_loss_streak:
            return False, f"loss streak {self.loss_streak} >= max {self.max_loss_streak}"

        # 6. Limite trades journaliers
        if self.daily_trades >= self.max_daily_trades:
            return False, f"daily trades {self.daily_trades} >= max {self.max_daily_trades}"

        # 7. Perte journalière
        daily_loss_pct = abs(min(0, self.daily_pnl)) / self.starting_capital
        if daily_loss_pct > self.max_daily_loss_pct:
            return False, f"daily loss {round(daily_loss_pct*100,2)}% > max {self.max_daily_loss_pct*100}%"

        # 8. Confidence minimum
        if confidence < 0.65:
            return False, f"confidence {confidence} < 0.65"

        return True, f"OK risk:{round(risk_pct*100,2)}%"

    def record_trade(self, pnl):
        """Enregistre le résultat d'un trade."""

        self.daily_trades += 1
        self.daily_pnl += pnl

        if pnl < 0:
            self.loss_streak += 1
        else:
            self.loss_streak = 0

    def _check_daily_reset(self):
        """Reset automatique des compteurs journaliers."""

        today = datetime.now(UTC).date()
        if today != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0
            self.loss_streak = 0
            self.last_reset_date = today

    def get_status(self):

        return {
            "loss_streak": self.loss_streak,
            "daily_trades": self.daily_trades,
            "daily_pnl": round(self.daily_pnl, 2),
        }
