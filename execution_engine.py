# execution_engine.py

import os
import random
import uuid
from datetime import datetime, UTC

from dotenv import load_dotenv

from position_manager import PositionManager
from risk_manager import RiskManager
from capital_manager import CapitalManager
from pnl_tracker import PnLTracker
from performance_tracker import PerformanceTracker

load_dotenv()


class ExecutionEngine:

    def __init__(self):
        self.orders = []
        self.mode = os.getenv("TRADING_MODE", "DRY")

        if self.mode == "LIVE":
            from polymarket_executor_live import PolymarketExecutorLive
            self.executor = PolymarketExecutorLive()
        else:
            from polymarket_executor import PolymarketExecutor
            self.executor = PolymarketExecutor(dry_run=True)

        self.position_manager = PositionManager(starting_capital=1000)
        self.risk_manager = RiskManager()
        self.capital_manager = CapitalManager(1000)
        self.pnl_tracker = PnLTracker()
        self.performance_tracker = PerformanceTracker()

    def create_order(self, market_title, side, price, size, token_id=None):

        order = {
            "order_id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),

            "market": market_title,
            "side": side,          # YES ou NO
            "price": price,
            "size": size,
            "token_id": token_id,

            "status": "CREATED"
        }

        self.orders.append(order)

        return order


    def execute_order(self, order):

        print("\n=== EXECUTION ENGINE ===")

        print(f"Order ID: {order['order_id']}")
        print(f"Market: {order['market']}")
        print(f"Side: {order['side']}")
        print(f"Price: {order['price']}")
        print(f"Size: {order['size']}")

        capital = self.position_manager.available_capital
        exposure = self.position_manager.get_total_exposure()

        approved = self.risk_manager.check_trade(
            capital,
            exposure,
            order["size"]
        )

        if not approved:

            print("Execution blocked by RiskManager")
            order["status"] = "BLOCKED_RISK"
            return order

        if not self.position_manager.can_open_position(order["size"]):

            print("\nEXECUTION BLOCKED: insufficient capital")
            order["status"] = "BLOCKED_CAPITAL"
            return order

        # MODE SAFE : pas d'envoi réel
        print("\nSTATUS: DRY RUN (no real trade)")

        order["status"] = "SIMULATED"

        self.position_manager.open_position(
            market=order["market"],
            side=order["side"],
            price=order["price"],
            size=order["size"]
        )

        self.executor.execute_order(
            market=order["market"],
            side=order["side"],
            price=order["price"],
            size=order["size"],
            token_id=order.get("token_id")
        )

        # simulation résultat trade
        result = random.choice(["win", "loss"])

        if result == "win":
            pnl = order["size"] * 0.1
        else:
            pnl = -order["size"] * 0.1

        self.pnl_tracker.record_trade(order["market"], pnl)
        self.performance_tracker.record_trade(pnl)
        self.capital_manager.update_capital(pnl)
        self.performance_tracker.report()

        return order


# test local
if __name__ == "__main__":

    engine = ExecutionEngine()

    order = engine.create_order(
        market_title="Cloud9 vs FlyQuest",
        side="YES",
        price=0.78,
        size=10
    )

    engine.execute_order(order)
