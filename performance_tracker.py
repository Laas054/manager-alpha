class PerformanceTracker:

    def __init__(self):

        self.total_trades = 0
        self.wins = 0
        self.losses = 0

        print("PerformanceTracker initialized")


    def record_trade(self, pnl):

        self.total_trades += 1

        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1


    def report(self):

        if self.total_trades == 0:

            return


        winrate = self.wins / self.total_trades


        print("\n=== PERFORMANCE REPORT ===")

        print("Trades:", self.total_trades)
        print("Wins:", self.wins)
        print("Losses:", self.losses)
        print("Winrate:", round(winrate * 100, 2), "%")
