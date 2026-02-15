class CapitalEngine:
    """Suivi du capital et drawdown."""

    def __init__(self, starting_capital=1000):

        self.starting = starting_capital
        self.current = starting_capital
        self.peak = starting_capital

        print(f"CapitalEngine initialized (capital: {starting_capital})")


    def update(self, pnl):

        self.current += pnl
        if self.current > self.peak:
            self.peak = self.current


    def get_drawdown(self):

        if self.peak == 0:
            return 0
        return round((self.peak - self.current) / self.peak, 4)


    def get_daily_return(self, daily_pnl):

        if self.starting == 0:
            return 0
        return round(daily_pnl / self.starting, 4)
