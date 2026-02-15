import os


class PolymarketExecutorLive:

    def __init__(self):

        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY", "")

        if not self.private_key or self.private_key == "your_private_key_here":
            print("  WARNING: No valid POLYMARKET_PRIVATE_KEY")
            self.client = None
            return

        from py_clob_client.client import ClobClient

        self.client = ClobClient(
            "https://clob.polymarket.com",
            key=self.private_key,
            chain_id=137
        )
        print("  PolymarketExecutorLive initialized")

    def execute(self, decision):

        if not self.client:
            print("  ERROR: No CLOB client")
            return {"pnl": 0, "status": "FAILED"}

        token_id = decision.get("token_id")
        if not token_id:
            print("  ERROR: token_id required for LIVE")
            return {"pnl": 0, "status": "FAILED"}

        from py_clob_client.clob_types import OrderArgs

        order = OrderArgs(
            price=decision["price"],
            size=decision["size"],
            side=decision["side"],
            token_id=token_id
        )

        signed_order = self.client.create_order(order)
        result = self.client.post_order(signed_order)

        print(f"  [LIVE] Order sent: {result}")

        return {
            "pnl": 0,
            "status": "LIVE",
            "result": result
        }
