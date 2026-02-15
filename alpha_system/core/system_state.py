from datetime import datetime, UTC


class SystemState:
    """État global du système — source unique de vérité."""

    def __init__(self, starting_capital=1000):

        self.starting_capital = starting_capital
        self.current_capital = starting_capital
        self.total_pnl = 0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.daily_pnl = 0
        self.peak_capital = starting_capital
        self.active = True
        self.started_at = datetime.now(UTC).isoformat()

        print("SystemState initialized | Capital:", starting_capital)


    def update_pnl(self, pnl):

        self.total_pnl += pnl
        self.daily_pnl += pnl
        self.current_capital += pnl
        self.total_trades += 1

        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1

        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital


    def get_drawdown(self):

        if self.peak_capital == 0:
            return 0
        return round((self.peak_capital - self.current_capital) / self.peak_capital, 4)


    def get_winrate(self):

        if self.total_trades == 0:
            return 0
        return round(self.wins / self.total_trades, 4)


    def reset_daily(self):

        self.daily_pnl = 0


    def shutdown(self):

        self.active = False


    def report(self):

        print("\n=== SYSTEM STATE ===")
        print(f"  Capital: {round(self.current_capital, 2)} (started: {self.starting_capital})")
        print(f"  Total PnL: {round(self.total_pnl, 2)}")
        print(f"  Trades: {self.total_trades} (W:{self.wins} L:{self.losses})")
        print(f"  Winrate: {round(self.get_winrate() * 100, 1)}%")
        print(f"  Drawdown: {round(self.get_drawdown() * 100, 2)}%")
        print(f"  Active: {self.active}")
