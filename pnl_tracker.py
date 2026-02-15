class PnLTracker:

    def __init__(self):

        self.total_pnl = 0
        self.trades = []

        print("PnLTracker initialized")


    def record_trade(self, market, pnl):

        trade = {

            "market": market,
            "pnl": pnl

        }

        self.trades.append(trade)

        self.total_pnl += pnl

        print("\nTrade recorded:", pnl)


    def get_total_pnl(self):

        return self.total_pnl


    def get_winrate(self):

        if not self.trades:
            return 0


        wins = sum(1 for t in self.trades if t["pnl"] > 0)

        return round(wins / len(self.trades), 2)
