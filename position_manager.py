from datetime import datetime, UTC


class PositionManager:

    def __init__(self, starting_capital=1000):

        self.starting_capital = starting_capital
        self.available_capital = starting_capital

        self.positions = {}

        print("PositionManager initialized")
        print("Capital:", self.available_capital)


    def can_open_position(self, size):

        return self.available_capital >= size


    def open_position(self, market, side, price, size):

        if not self.can_open_position(size):

            print("ERROR: Not enough capital")
            return False


        position = {

            "market": market,
            "side": side,
            "price": price,
            "size": size,
            "timestamp": datetime.now(UTC).isoformat()

        }

        self.positions[market] = position

        self.available_capital -= size

        print("\nPOSITION OPENED")
        print("Market:", market)
        print("Size:", size)
        print("Remaining capital:", self.available_capital)

        return True


    def close_position(self, market, exit_price):

        if market not in self.positions:

            print("No position found")
            return


        position = self.positions[market]

        pnl = (exit_price - position["price"]) * position["size"]

        self.available_capital += position["size"] + pnl

        print("\nPOSITION CLOSED")
        print("PnL:", pnl)
        print("Capital:", self.available_capital)

        del self.positions[market]


    def get_total_exposure(self):

        total = 0

        for p in self.positions.values():
            total += p["size"]

        return total


    def show_positions(self):

        print("\n=== OPEN POSITIONS ===")

        for market, pos in self.positions.items():

            print(
                market,
                pos["side"],
                pos["size"],
                pos["price"]
            )
