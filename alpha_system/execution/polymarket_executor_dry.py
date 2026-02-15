import uuid
import random


class PolymarketExecutorDry:

    def execute(self, decision):

        size = decision.get("size", 1)
        confidence = decision.get("confidence", 0.5)

        # Simulation realiste basee sur la confiance
        winrate = 0.52 + (confidence - 0.5) * 0.2
        win = random.random() < winrate

        if win:
            pnl = round(size * 0.1, 2)
        else:
            pnl = round(-size * 0.1, 2)

        print(f"  [DRY] SIMULATED | PnL: {pnl}")

        return {
            "id": str(uuid.uuid4()),
            "pnl": pnl,
            "status": "SIMULATED"
        }
