from alpha_system.config import MAX_RISK_PER_TRADE, MAX_EXPOSURE, MAX_POSITION_SIZE


class RiskManager:

    def __init__(self):

        self.max_risk_per_trade_pct = MAX_RISK_PER_TRADE
        self.max_total_exposure_pct = MAX_EXPOSURE
        self.max_position_size = MAX_POSITION_SIZE

        print("RiskManager initialized")


    def check_trade(self, capital, current_exposure, trade_size):

        print("\n=== RISK CHECK ===")

        risk_pct = trade_size / capital
        exposure_pct = (current_exposure + trade_size) / capital

        print("Risk per trade:", round(risk_pct * 100, 2), "%")
        print("Total exposure:", round(exposure_pct * 100, 2), "%")

        if trade_size > self.max_position_size:
            print("BLOCKED: position too large")
            return False

        if risk_pct > self.max_risk_per_trade_pct:
            print("BLOCKED: risk per trade too high")
            return False

        if exposure_pct > self.max_total_exposure_pct:
            print("BLOCKED: total exposure too high")
            return False

        print("RISK APPROVED")
        return True
