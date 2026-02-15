from alpha_system.config import CONFIG


class RiskEngine:

    def __init__(self):
        self.max_risk = CONFIG["MAX_RISK_PER_TRADE"]
        self.max_trade_size = CONFIG["MAX_TRADE_SIZE"]

    def validate(self, capital, size):

        if size > self.max_trade_size:
            print(f"  [RISK] BLOCKED: size {size} > max {self.max_trade_size}")
            return False

        if capital <= 0:
            print("  [RISK] BLOCKED: no capital")
            return False

        risk = size / capital
        if risk > self.max_risk:
            print(f"  [RISK] BLOCKED: risk {round(risk*100,2)}% > max {self.max_risk*100}%")
            return False

        print(f"  [RISK] OK | size:{size} risk:{round(risk*100,2)}%")
        return True
