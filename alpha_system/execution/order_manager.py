import uuid
from datetime import datetime, UTC


class OrderManager:
    """Crée et gère les ordres."""

    def __init__(self):

        self.orders = []
        self.order_history = []

        print("OrderManager initialized")


    def create(self, market, side, price, size, token_id=None):

        order = {
            "order_id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "market": market,
            "side": side,
            "price": price,
            "size": size,
            "token_id": token_id,
            "status": "CREATED"
        }

        self.orders.append(order)
        return order


    def finalize(self, order, status, pnl=0):

        order["status"] = status
        order["pnl"] = pnl
        self.order_history.append(order)
