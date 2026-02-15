class CostCalculator:
    """Calcul frais, slippage, validation rentabilité."""

    def __init__(self, config):

        self.maker_fee = config["MAKER_FEE"]
        self.taker_fee = config["TAKER_FEE"]
        self.base_slippage = config["BASE_SLIPPAGE"]
        self.max_slippage = config["MAX_SLIPPAGE"]

    def calculate_total_cost(self, size, price):
        """Calcule le coût total d'un trade (frais + slippage)."""

        fee = size * self.taker_fee
        slippage = self.estimate_slippage(size, price)
        total = round(fee + slippage, 4)

        return {
            "fee": round(fee, 4),
            "slippage": round(slippage, 4),
            "total_cost": total,
        }

    def estimate_slippage(self, size, price):
        """Estime le slippage en fonction de la taille et du prix."""

        # Plus la taille est grande, plus le slippage augmente
        size_factor = min(size / 100, 1.0)
        slippage_pct = self.base_slippage + (self.max_slippage - self.base_slippage) * size_factor

        return round(size * slippage_pct, 4)

    def adjust_pnl(self, raw_pnl, size, price):
        """Ajuste le PnL en retirant les frais réels."""

        costs = self.calculate_total_cost(size, price)
        adjusted = round(raw_pnl - costs["total_cost"], 4)

        return {
            "raw_pnl": round(raw_pnl, 4),
            "adjusted_pnl": adjusted,
            "costs": costs,
        }

    def is_trade_worth_it(self, size, price, confidence):
        """Vérifie si le trade est rentable après tous les frais."""

        costs = self.calculate_total_cost(size, price)

        edge = abs(price - 0.5)
        expected_gain = size * edge * confidence
        expected_net = expected_gain - costs["total_cost"]

        return {
            "worth_it": expected_net > 0,
            "expected_gain": round(expected_gain, 4),
            "expected_net": round(expected_net, 4),
            "costs": costs,
        }

    def validate(self, decision):
        """Valide la rentabilité d'une décision. Retourne (ok, info)."""

        size = decision.get("size", 1)
        price = decision.get("price", 0.5)
        confidence = decision.get("confidence", 0)

        result = self.is_trade_worth_it(size, price, confidence)

        if not result["worth_it"]:
            return False, f"not profitable: net={result['expected_net']}"

        return True, f"net={result['expected_net']} costs={result['costs']['total_cost']}"
