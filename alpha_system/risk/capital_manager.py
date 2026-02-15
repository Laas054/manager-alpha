from alpha_system.config import STARTING_CAPITAL


class CapitalManager:

    def __init__(self, starting_capital=None):

        self.starting_capital = starting_capital or STARTING_CAPITAL
        self.current_capital = self.starting_capital

        print("CapitalManager initialized")
        print("Capital:", self.current_capital)


    def update_capital(self, pnl):

        self.current_capital += pnl
        print("\nCapital updated:", round(self.current_capital, 2))


    def get_capital(self):

        return self.current_capital


    def get_drawdown(self):

        if self.starting_capital == 0:
            return 0

        drawdown = (
            self.starting_capital - self.current_capital
        ) / self.starting_capital

        return round(drawdown, 4)
