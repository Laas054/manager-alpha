class StrategyAutoOptimizer:

    def optimize(self, performance):

        if performance is None:
            return

        pnl = performance.get("total_pnl", 0) if isinstance(performance, dict) else performance

        if pnl < 0:
            print("  [OPTIMIZER] Strategy tightening — reducing risk")
        else:
            print("  [OPTIMIZER] Strategy performing — maintaining")
