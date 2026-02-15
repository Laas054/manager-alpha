import random


class PaperTradingEngine:
    """Simulation réaliste de trades — remplace le random brut."""

    def __init__(self, base_winrate=0.52, slippage=0.01):

        self.base_winrate = base_winrate
        self.slippage = slippage
        self.total_simulated = 0

        print(f"PaperTradingEngine initialized (winrate:{base_winrate} slippage:{slippage})")


    def execute(self, decision):
        """Simule un trade avec PnL réaliste basé sur la confiance."""

        self.total_simulated += 1

        size = decision.get("size", 1)
        confidence = decision.get("confidence", 0.5)
        price = decision.get("price", 0.5)

        # Winrate ajusté par la confiance de l'IA
        adjusted_winrate = self.base_winrate + (confidence - 0.5) * 0.2

        win = random.random() < adjusted_winrate

        if win:
            # Gain basé sur le prix (plus le prix est extrême, plus le gain potentiel est faible)
            edge = abs(price - 0.5)
            gain_pct = max(0.05, 0.15 - edge * 0.1)
            pnl = round(size * gain_pct, 2)
        else:
            # Perte avec slippage
            loss_pct = random.uniform(0.05, 0.15) + self.slippage
            pnl = round(-size * loss_pct, 2)

        return pnl
