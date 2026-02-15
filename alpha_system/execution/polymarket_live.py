import os


class PolymarketLive:
    """Connecteur réel Polymarket via py-clob-client."""

    def __init__(self):

        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY", "")

        if not self.private_key or self.private_key == "your_private_key_here":
            print("PolymarketLive: no valid key — orders will fail in LIVE mode")
            self.client = None
            return

        from py_clob_client.client import ClobClient

        self.client = ClobClient(
            "https://clob.polymarket.com",
            key=self.private_key,
            chain_id=137
        )

        print("PolymarketLive initialized")


    def place_order(self, token_id, side, price, size):

        if not self.client:
            print("ERROR: No CLOB client — cannot place LIVE order")
            return None

        if not token_id:
            print("ERROR: token_id required")
            return None

        from py_clob_client.clob_types import OrderArgs

        order = OrderArgs(
            price=price,
            size=size,
            side=side,
            token_id=token_id
        )

        signed_order = self.client.create_order(order)
        result = self.client.post_order(signed_order)

        print("LIVE order sent:", result)
        return result
