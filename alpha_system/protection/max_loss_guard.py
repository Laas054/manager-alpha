from alpha_system.config import MAX_DAILY_LOSS


class MaxLossGuard:

    def __init__(self):

        self.max_daily_loss = MAX_DAILY_LOSS
        self.daily_pnl = 0

        print("MaxLossGuard initialized (max daily loss:", self.max_daily_loss, ")")


    def record(self, pnl):

        self.daily_pnl += pnl


    def check(self, starting_capital):

        if starting_capital == 0:
            return True

        daily_loss_pct = abs(min(0, self.daily_pnl)) / starting_capital

        if daily_loss_pct > self.max_daily_loss:

            print(f"\nMAX DAILY LOSS EXCEEDED: {round(daily_loss_pct * 100, 2)}%")
            return False

        return True


    def reset_daily(self):

        self.daily_pnl = 0
