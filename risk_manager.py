class RiskManager:

    def __init__(self):

        self.max_risk_per_trade_pct = 0.02      # 2%
        self.max_total_exposure_pct = 0.20      # 20%
        self.max_position_size = 100            # limite brute

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
