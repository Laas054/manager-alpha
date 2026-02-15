from alpha_system.config import CONFIG
from alpha_system.utils.logger import Logger
from alpha_system.memory.database import DatabaseManager
from alpha_system.protection.error_handler import ErrorHandler
from alpha_system.protection.kill_switch import KillSwitch
from alpha_system.market.polymarket_reader import PolymarketReader
from alpha_system.market.adaptive_scanner import AdaptiveScanner
from alpha_system.ai.secure_ai_client import SecureAIClient
from alpha_system.ai.confidence_manager import ConfidenceManager
from alpha_system.ai.profit_optimizer import ProfitOptimizer
from alpha_system.execution.execution_engine import ExecutionEngine
from alpha_system.execution.cost_calculator import CostCalculator
from alpha_system.execution.position_manager import PositionManager
from alpha_system.execution.position_monitor import PositionMonitor
from alpha_system.execution.wallet_monitor import WalletMonitor
from alpha_system.execution.order_monitor import OrderMonitor
from alpha_system.execution.execution_guard import ExecutionGuard
from alpha_system.execution.live_execution_orchestrator import LiveExecutionOrchestrator
from alpha_system.risk.risk_engine_v2 import RiskEngineV2


class AlphaOrchestrator:
    """Orchestrator final — pipeline complet sécurisé."""

    def __init__(self):

        # Logger (premier — utilisé par tout)
        self.log = Logger()
        self.log.info("Initializing Trading Bot Alpha...")

        # Database
        self.db = DatabaseManager(CONFIG["DB_PATH"])

        # Error handler
        self.errors = ErrorHandler(logger=self.log, db=self.db)

        # Market
        self.reader = PolymarketReader()
        self.scanner = AdaptiveScanner(config=CONFIG)

        # AI
        self.ai_clients = [
            SecureAIClient(CONFIG),
            SecureAIClient(CONFIG),
            SecureAIClient(CONFIG),
        ]
        self.ai_models = ["deepseek-v3.2", "qwen3-next:80b", "glm-5"]
        self.confidence = ConfidenceManager(CONFIG)
        self.optimizer = ProfitOptimizer()

        # Cost & Risk (before execution — needed by position manager)
        self.cost_calc = CostCalculator(CONFIG)
        self.risk = RiskEngineV2(CONFIG)
        self.kill_switch = KillSwitch()

        # Position Manager (before execution — passed to live executor)
        self.positions = PositionManager(
            risk_engine=self.risk,
            database=self.db,
            cost_calc=self.cost_calc,
            logger=self.log,
        )

        # Execution (receives position_manager for LIVE mode)
        self.execution = ExecutionEngine(
            position_manager=self.positions,
            logger=self.log,
            database=self.db,
        )
        self.positions.execution = self.execution

        # Live Execution modules
        self.wallet = WalletMonitor(
            polymarket_client=getattr(self.execution.executor, 'client', None),
            logger=self.log,
            database=self.db,
        )
        self.order_monitor = OrderMonitor(
            polymarket_client=getattr(self.execution.executor, 'client', None),
            logger=self.log,
            database=self.db,
        )
        self.guard = ExecutionGuard(
            config=CONFIG,
            logger=self.log,
            database=self.db,
        )
        self.live_exec = LiveExecutionOrchestrator(
            executor=self.execution,
            position_manager=self.positions,
            wallet_monitor=self.wallet,
            guard=self.guard,
            order_monitor=self.order_monitor,
            logger=self.log,
            database=self.db,
        )

        # Position Monitor (WebSocket temps réel)
        self.monitor = PositionMonitor(
            position_manager=self.positions,
            logger=self.log,
            database=self.db,
        )

        # State
        self.capital = CONFIG["STARTING_CAPITAL"]
        self.starting_capital = CONFIG["STARTING_CAPITAL"]
        self.total_pnl = 0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0

        # Restore state
        saved = self.db.load_state()
        if saved:
            self.capital = saved["capital"]
            self.starting_capital = saved["starting_capital"]
            self.total_pnl = saved["total_pnl"]
            self.total_trades = saved["total_trades"]
            self.wins = saved["wins"]
            self.losses = saved["losses"]
            self.log.info(f"State restored | Capital: {self.capital} | Trades: {self.total_trades}")
        else:
            self.log.info(f"Fresh start | Capital: {self.capital}")

        self.log.info("System initialized.")

    def cycle(self):
        """Un cycle complet : scan -> AI -> validate -> execute -> record."""

        # 0. Error handler check
        if not self.errors.is_system_healthy():
            self.log.critical("System unhealthy — too many critical errors")
            return "UNHEALTHY"

        # 1. Kill switch
        if not self.kill_switch.validate(self.capital, self.starting_capital):
            self.log.critical(f"KILL SWITCH — capital: {self.capital}")
            self.db.log_audit("KILL_SWITCH", f"capital={self.capital}")
            return "KILLED"

        # 2. Scan markets
        markets = self.errors.safe_execute(
            self.reader.get_markets, default=[], context="market_scan"
        )

        if not markets:
            self.scanner.record_scan(0)
            return "NO_MARKETS"

        self.scanner.record_scan(len(markets))
        self.log.info(f"{len(markets)} markets fetched")

        # Sort by volume
        markets.sort(key=lambda x: x.get("volume", 0), reverse=True)

        # 3. Evaluate top markets
        for market in markets[:3]:

            decision = self._evaluate_market(market)

            if decision is None:
                continue

            # 4. Confidence check
            conf_ok, conf_reason = self.confidence.validate(decision)
            if not conf_ok:
                self.log.debug(f"Confidence rejected: {conf_reason}")
                continue

            # 5. Calculate size
            size = self.optimizer.calculate_size(
                self.capital, decision["confidence"]
            )
            decision["size"] = size

            # 6. Cost check
            cost_ok, cost_info = self.cost_calc.validate(decision)
            if not cost_ok:
                self.log.debug(f"Cost rejected: {cost_info}")
                continue

            # 7. Risk check
            risk_ok, risk_reason = self.risk.validate_trade(
                self.capital, size, decision["confidence"]
            )
            if not risk_ok:
                self.log.risk(f"Blocked: {risk_reason}")
                self.db.log_audit("RISK_BLOCKED", risk_reason)
                continue

            # 8. Execute (via full pipeline: guard -> wallet -> execute -> fill)
            order = self.errors.safe_execute(
                self.live_exec.execute, decision,
                default=None, context="execution"
            )

            if order is None:
                continue

            pnl = order.get("pnl", 0)

            # 9. Update state
            self.capital += pnl
            self.total_pnl += pnl
            self.total_trades += 1

            if pnl > 0:
                self.wins += 1
            else:
                self.losses += 1

            self.risk.record_trade(pnl)
            self.risk.update_capital(self.capital)

            # Confidence outcome for auto-adjust
            self.confidence.record_outcome(decision["confidence"], pnl > 0)

            # 10. Record in database
            self.db.record_trade(
                market=decision["market"],
                side=decision["side"],
                price=decision["price"],
                size=size,
                pnl=pnl,
                confidence=decision["confidence"],
                model=decision.get("model", ""),
                source=decision.get("source", "ai"),
                status=order.get("status", "SIMULATED"),
            )

            self._save_state()

            # 11. Log
            self.log.trade(
                decision["market"], decision["side"],
                size, pnl, decision["confidence"]
            )
            self.db.log_audit(
                "EXECUTED",
                f"pnl={round(pnl,2)} capital={round(self.capital,2)}"
            )

            self.log.info(f"PnL: {round(pnl, 2)} | Capital: {round(self.capital, 2)}")

            # Un seul trade par cycle
            return "EXECUTED"

        return "NO_TRADE"

    def _evaluate_market(self, market):
        """Évalue un marché via l'ensemble IA."""

        results = []
        for client, model in zip(self.ai_clients, self.ai_models):
            result = self.errors.safe_execute(
                client.evaluate, market, model,
                default={"trade": False, "side": "NO", "confidence": 0},
                context=f"ai_{model}"
            )
            results.append(result)
            trade = result.get("trade", False)
            conf = result.get("confidence", 0)
            self.log.debug(f"  [{model}] trade:{trade} conf:{conf}")

        # Filtrer trades
        trades = [r for r in results if r.get("trade", False)]

        if not trades:
            return None

        # Meilleure confiance
        best = max(trades, key=lambda x: x.get("confidence", 0))

        decision = {
            "market": market["market"],
            "token_id": market.get("token_id"),
            "side": best["side"],
            "confidence": best["confidence"],
            "price": market["price"],
            "volume": market.get("volume", 0),
            "model": best.get("model", ""),
            "source": best.get("source", "ai"),
        }

        return decision

    def _save_state(self):

        self.db.save_state(
            capital=round(self.capital, 2),
            starting_capital=self.starting_capital,
            total_pnl=round(self.total_pnl, 2),
            total_trades=self.total_trades,
            wins=self.wins,
            losses=self.losses,
        )

    def report(self):

        winrate = round(self.wins / max(1, self.total_trades) * 100, 1)
        drawdown = round(
            (self.starting_capital - self.capital) / max(1, self.starting_capital) * 100, 2
        )

        self.log.info("=" * 50)
        self.log.info("TRADING BOT ALPHA REPORT")
        self.log.info(f"  Capital: {round(self.capital, 2)} (started: {self.starting_capital})")
        self.log.info(f"  Total PnL: {round(self.total_pnl, 2)}")
        self.log.info(f"  Trades: {self.total_trades} (W:{self.wins} L:{self.losses})")
        self.log.info(f"  Winrate: {winrate}%")
        self.log.info(f"  Drawdown: {drawdown}%")

        # AI benchmark
        for client, model in zip(self.ai_clients, self.ai_models):
            bench = client.get_benchmark()
            self.log.info(f"  AI [{model}]: {bench['success_rate']}% success, {bench['avg_latency']}s avg")

        # Risk status
        risk_status = self.risk.get_status()
        self.log.info(f"  Risk: streak:{risk_status['loss_streak']} daily:{risk_status['daily_trades']} hourly:{risk_status['hourly_trades']}")
        self.log.info(f"  Peak capital: {risk_status['peak_capital']} | Open positions: {risk_status['open_positions']}")

        # Position Manager status
        pos_status = self.positions.get_status()
        self.log.info(f"  Positions: {pos_status['open_count']} open, {pos_status['closed_count']} closed")
        self.log.info(f"  Exposure: {pos_status['total_exposure']} | Unrealized PnL: {pos_status['unrealized_pnl']}")

        # Live Execution status
        live_status = self.live_exec.get_status()
        self.log.info(f"  Execution: signals:{live_status['total_signals']} executed:{live_status['executed']} guard_blocked:{live_status['guard_blocked']} wallet_blocked:{live_status['wallet_blocked']}")

        # Wallet status
        wallet_status = self.wallet.get_status()
        self.log.info(f"  Wallet: balance:{wallet_status['balance']} checks:{wallet_status['checks_total']} blocked:{wallet_status['checks_blocked']}")

        # Position Monitor status
        mon_status = self.monitor.get_status()
        self.log.info(f"  Monitor: connected:{mon_status['connected']} updates:{mon_status['price_updates']} exits:{mon_status['exits_triggered']}")

        # Scanner status
        scan_status = self.scanner.get_status()
        self.log.info(f"  Scanner: interval:{scan_status['interval']}s rate_limited:{scan_status['rate_limited']}")

        # Error status
        err_status = self.errors.get_status()
        self.log.info(f"  Errors: {err_status['total_errors']} total, {err_status['critical_errors']} critical")

        self.log.info("=" * 50)

        # DB stats
        stats = self.db.get_stats()
        if stats:
            self.log.info(f"  DB: {stats['total']} trades, avg_conf: {stats.get('avg_confidence', 0)}")

    def shutdown(self):
        """Arrêt propre."""

        self.log.info("Shutting down...")
        self._save_state()
        self.db.backup()
        self.db.close()
        self.log.info("Shutdown complete.")
