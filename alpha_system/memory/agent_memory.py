class AgentMemory:
    """Suit la performance de chaque agent IA."""

    def __init__(self):

        self.agents = {}

        print("AgentMemory initialized")


    def record(self, model, pnl):

        if model not in self.agents:
            self.agents[model] = {"wins": 0, "losses": 0, "total_pnl": 0}

        self.agents[model]["total_pnl"] += pnl

        if pnl > 0:
            self.agents[model]["wins"] += 1
        else:
            self.agents[model]["losses"] += 1


    def get_best_agent(self):

        if not self.agents:
            return None

        return max(self.agents.items(), key=lambda x: x[1]["total_pnl"])


    def report(self):

        print("\n=== AGENT PERFORMANCE ===")
        if not self.agents:
            print("  (no data)")
            return

        for model, stats in sorted(
            self.agents.items(),
            key=lambda x: x[1]["total_pnl"],
            reverse=True
        ):
            total = stats["wins"] + stats["losses"]
            wr = round(stats["wins"] / total * 100, 1) if total > 0 else 0
            print(f"  {model}: PnL:{round(stats['total_pnl'],2)} "
                  f"W:{stats['wins']} L:{stats['losses']} WR:{wr}%")
