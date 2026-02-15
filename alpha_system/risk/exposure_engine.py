from datetime import datetime, UTC


class ExposureEngine:
    """Gestion des positions et exposition."""

    def __init__(self, starting_capital=1000):

        self.available = starting_capital
        self.positions = {}

        print(f"ExposureEngine initialized (capital: {starting_capital})")


    def can_open(self, size):

        return self.available >= size


    def open_position(self, market, side, price, size):

        if not self.can_open(size):
            return False

        self.positions[market] = {
            "side": side,
            "price": price,
            "size": size,
            "timestamp": datetime.now(UTC).isoformat()
        }

        self.available -= size

        print(f"\n  POSITION OPENED: {market}")
        print(f"  Size: {size} | Remaining: {round(self.available, 2)}")
        return True


    def close_position(self, market, exit_price):

        if market not in self.positions:
            return 0

        pos = self.positions[market]
        pnl = (exit_price - pos["price"]) * pos["size"]
        self.available += pos["size"] + pnl

        del self.positions[market]
        return pnl


    def get_total_exposure(self):

        return sum(p["size"] for p in self.positions.values())


    def show(self):

        print("\n=== POSITIONS ===")
        if not self.positions:
            print("  (none)")
            return
        for m, p in self.positions.items():
            print(f"  {m} | {p['side']} | size:{p['size']} | price:{p['price']}")
