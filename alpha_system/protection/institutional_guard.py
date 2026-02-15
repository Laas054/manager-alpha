from alpha_system.config import CONFIG


class InstitutionalGuard:
    """Protection institutionnelle — limites strictes."""

    def __init__(self):
        self.daily_pnl = 0
        self.daily_trades = 0
        self.max_daily_loss = CONFIG["STARTING_CAPITAL"] * 0.05
        self.max_daily_trades = 50

    def record(self, pnl):
        self.daily_pnl += pnl
        self.daily_trades += 1

    def validate(self):

        if self.daily_pnl < -self.max_daily_loss:
            print(f"  [GUARD] Daily loss limit: {round(self.daily_pnl, 2)}")
            return False

        if self.daily_trades >= self.max_daily_trades:
            print(f"  [GUARD] Max daily trades reached: {self.daily_trades}")
            return False

        return True

    def reset_daily(self):
        self.daily_pnl = 0
        self.daily_trades = 0
