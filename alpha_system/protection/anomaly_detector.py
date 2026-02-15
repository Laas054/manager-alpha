class AnomalyDetector:
    """Détecte les anomalies de trading."""

    def __init__(self, max_consecutive_losses=5, max_daily_loss_pct=0.05):

        self.max_consecutive_losses = max_consecutive_losses
        self.max_daily_loss_pct = max_daily_loss_pct
        self.consecutive_losses = 0

        print(f"AnomalyDetector initialized (max_consec_loss:{max_consecutive_losses})")


    def record(self, pnl):

        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0


    def check(self, state):

        # Série de pertes
        if self.consecutive_losses >= self.max_consecutive_losses:
            print(f"\n  ANOMALY: {self.consecutive_losses} consecutive losses!")
            return False

        # Perte journalière
        if state.starting_capital > 0:
            daily_loss_pct = abs(min(0, state.daily_pnl)) / state.starting_capital
            if daily_loss_pct > self.max_daily_loss_pct:
                print(f"\n  ANOMALY: daily loss {round(daily_loss_pct*100,2)}% exceeds limit")
                return False

        return True


    def reset_daily(self):
        self.consecutive_losses = 0
