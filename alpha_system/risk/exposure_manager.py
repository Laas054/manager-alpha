from datetime import datetime, UTC


class ExposureManager:

    def __init__(self, starting_capital=1000):

        self.starting_capital = starting_capital
        self.available_capital = starting_capital
        self.positions = {}

        print("ExposureManager initialized")
        print("Capital:", self.available_capital)


    def can_open_position(self, size):

        return self.available_capital >= size


    def open_position(self, market, side, price, size):

        if not self.can_open_position(size):
            print("ERROR: Not enough capital")
            return False

        self.positions[market] = {
            "market": market,
            "side": side,
            "price": price,
            "size": size,
            "timestamp": datetime.now(UTC).isoformat()
        }

        self.available_capital -= size

        print("\nPOSITION OPENED")
        print("Market:", market)
        print("Size:", size)
        print("Remaining capital:", round(self.available_capital, 2))

        return True


    def close_position(self, market, exit_price):

        if market not in self.positions:
            print("No position found")
            return 0

        position = self.positions[market]
        pnl = (exit_price - position["price"]) * position["size"]

        self.available_capital += position["size"] + pnl

        print("\nPOSITION CLOSED")
        print("PnL:", round(pnl, 2))
        print("Capital:", round(self.available_capital, 2))

        del self.positions[market]
        return pnl


    def get_total_exposure(self):

        return sum(p["size"] for p in self.positions.values())


    def show_positions(self):

        print("\n=== OPEN POSITIONS ===")

        if not self.positions:
            print("  (none)")
            return

        for market, pos in self.positions.items():
            print(f"  {market} | {pos['side']} | size:{pos['size']} | price:{pos['price']}")
