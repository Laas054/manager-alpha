class PerformanceMemory:
    """Suggère des améliorations basées sur l'historique."""

    def __init__(self, trade_memory):

        self.memory = trade_memory

        print("PerformanceMemory initialized")


    def suggest_min_confidence(self):

        avg_win = self.memory.get_avg_confidence(wins_only=True)
        avg_loss = self.memory.get_avg_confidence(wins_only=False)

        if avg_win == 0:
            return 0.70

        suggested = (avg_win + avg_loss) / 2
        return round(max(0.50, min(0.95, suggested)), 2)


    def report(self):

        total = len(self.memory.trades)
        if total == 0:
            print("\n  No trade history for optimization")
            return

        wins = sum(1 for t in self.memory.trades if t["won"])
        suggested = self.suggest_min_confidence()

        print(f"\n=== OPTIMIZER ===")
        print(f"  Trades: {total} | Wins: {wins} | Losses: {total - wins}")
        print(f"  Avg confidence (wins): {round(self.memory.get_avg_confidence(True), 2)}")
        print(f"  Avg confidence (losses): {round(self.memory.get_avg_confidence(False), 2)}")
        print(f"  Suggested min confidence: {suggested}")
