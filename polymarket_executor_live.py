from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
import os


class PolymarketExecutorLive:

    def __init__(self):

        self.host = "https://clob.polymarket.com"

        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY")

        if not self.private_key:

            raise Exception("Missing private key")


        self.client = ClobClient(

            self.host,
            key=self.private_key,
            chain_id=137

        )

        print("LIVE executor initialized")


    def execute_order(self, market, side, price, size, token_id=None):

        print("\n=== LIVE ORDER ===")

        if not token_id:
            print("ERROR: token_id required for LIVE trading")
            return None

        order = OrderArgs(

            price=price,
            size=size,
            side=side,
            token_id=token_id

        )

        signed_order = self.client.create_order(order)

        result = self.client.post_order(signed_order)

        print("Order sent:", result)

        return result
