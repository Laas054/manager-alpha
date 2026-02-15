class CapitalManager:

    def __init__(self, starting_capital=1000):

        self.starting_capital = starting_capital
        self.current_capital = starting_capital

        print("CapitalManager initialized")
        print("Capital:", self.current_capital)


    def update_capital(self, pnl):

        self.current_capital += pnl

        print("\nCapital updated:", self.current_capital)


    def get_capital(self):

        return self.current_capital


    def get_drawdown(self):

        drawdown = (
            self.starting_capital - self.current_capital
        ) / self.starting_capital

        return round(drawdown, 4)
