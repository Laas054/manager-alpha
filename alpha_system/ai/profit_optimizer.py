from alpha_system.config import CONFIG


class ProfitOptimizer:

    def calculate_size(self, capital, confidence):
        base = capital * 0.01
        size = round(base * confidence, 2)

        # Respecter MAX_TRADE_SIZE
        max_size = CONFIG["MAX_TRADE_SIZE"]
        if size > max_size:
            size = max_size

        return max(0.1, size)
