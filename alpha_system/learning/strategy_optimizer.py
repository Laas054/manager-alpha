class StrategyOptimizer:

    def __init__(self, trade_memory):

        self.memory = trade_memory

        print("StrategyOptimizer initialized")


    def suggest_min_confidence(self):
        """Suggère un seuil de confidence basé sur l'historique."""

        avg_win = self.memory.get_avg_confidence_for_wins()
        avg_loss = self.memory.get_avg_confidence_for_losses()

        if avg_win == 0:
            return 0.60  # défaut

        # seuil = moyenne entre wins et losses
        suggested = (avg_win + avg_loss) / 2

        return round(max(0.50, min(0.95, suggested)), 2)


    def report(self):

        total = len(self.memory.trades)

        if total == 0:
            print("\nNo trades in memory yet")
            return

        wins = sum(1 for t in self.memory.trades if t["won"])
        losses = total - wins

        avg_win_conf = self.memory.get_avg_confidence_for_wins()
        avg_loss_conf = self.memory.get_avg_confidence_for_losses()
        suggested = self.suggest_min_confidence()

        print("\n=== STRATEGY OPTIMIZER ===")
        print(f"Total trades: {total}")
        print(f"Wins: {wins} | Losses: {losses}")
        print(f"Avg confidence (wins): {round(avg_win_conf, 2)}")
        print(f"Avg confidence (losses): {round(avg_loss_conf, 2)}")
        print(f"Suggested min confidence: {suggested}")
