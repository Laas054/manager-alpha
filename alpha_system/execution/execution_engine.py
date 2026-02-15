import uuid
from datetime import datetime, UTC

from alpha_system.config import CONFIG


class ExecutionEngine:

    def __init__(self, position_manager=None, logger=None, database=None):
        mode = CONFIG["MODE"]
        self.mode = mode

        if mode == "LIVE":
            from alpha_system.execution.polymarket_executor_live import PolymarketExecutorLive
            self.executor = PolymarketExecutorLive(
                position_manager=position_manager,
                logger=logger,
                database=database,
            )
        else:
            from alpha_system.execution.polymarket_executor_dry import PolymarketExecutorDry
            self.executor = PolymarketExecutorDry()

    def execute(self, decision):

        order = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "market": decision["market"],
            "side": decision["side"],
            "price": decision["price"],
            "size": decision.get("size", 1),
            "token_id": decision.get("token_id"),
        }

        result = self.executor.execute(decision)

        order["pnl"] = result.get("pnl", 0)
        order["status"] = result.get("status", "SIMULATED")

        return order
