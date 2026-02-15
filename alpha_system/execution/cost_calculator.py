class CostCalculator:
    """Calcul des frais, slippage, validation rentabilité."""

    def __init__(self):

        # Polymarket fees
        self.maker_fee = 0.0     # 0% maker
        self.taker_fee = 0.02    # 2% taker
        self.slippage_pct = 0.01  # 1% slippage estimé

    def calculate_costs(self, size, price):
        """Calcule le coût total d'un trade."""

        fee = size * self.taker_fee
        slippage = size * self.slippage_pct
        total_cost = round(fee + slippage, 4)

        return {
            "fee": round(fee, 4),
            "slippage": round(slippage, 4),
            "total_cost": total_cost,
        }

    def is_profitable(self, size, price, confidence):
        """Vérifie si le trade est rentable après frais."""

        costs = self.calculate_costs(size, price)

        # Gain espéré = size * edge * confidence
        edge = abs(price - 0.5)
        expected_gain = size * edge * confidence
        expected_net = expected_gain - costs["total_cost"]

        return {
            "profitable": expected_net > 0,
            "expected_gain": round(expected_gain, 4),
            "expected_net": round(expected_net, 4),
            "costs": costs,
        }

    def validate(self, decision):
        """Valide la rentabilité d'une décision. Retourne (ok, info)."""

        size = decision.get("size", 1)
        price = decision.get("price", 0.5)
        confidence = decision.get("confidence", 0)

        result = self.is_profitable(size, price, confidence)

        if not result["profitable"]:
            return False, f"not profitable: net={result['expected_net']}"

        return True, f"net={result['expected_net']} costs={result['costs']['total_cost']}"
