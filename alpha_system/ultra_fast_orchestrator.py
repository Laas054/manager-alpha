"""
Ultra Fast Orchestrator — Pipeline parallèle basse latence.

Thread 1: Scanner continu Polymarket
Thread 2: Decision engine (AI + Risk + Execution)
Main:     Monitoring + Reports + Shutdown

Latence cible: 50-150ms (hors appels IA)
"""

import threading
import queue
import time
from datetime import datetime, timezone

from alpha_system.config import CONFIG
from alpha_system.utils.logger import setup_logger
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
from alpha_system.risk.risk_engine_v2 import RiskEngineV2


# ============================================
# CONFIGURATION ULTRA FAST
# ============================================

SCAN_DELAY = 0.05       # 50 ms entre scans
MAX_QUEUE_SIZE = 1000
AI_MODELS = ["deepseek-v3.2", "qwen3-next:80b", "glm-5"]
REPORT_INTERVAL = 60     # report toutes les 60s
BACKUP_INTERVAL = 600    # backup toutes les 10 min


# ============================================
# FAST FILTER (instantané, ~1ms)
# ============================================

class FastFilter:
    """Filtre pré-IA ultra rapide — élimine les marchés inutiles."""

    def __init__(self):
        self.min_volume = 1000
        self.min_price = 0.05
        self.max_price = 0.95
        self.recently_seen = {}
        self.cooldown = 300  # 5 min avant de réévaluer un marché

    def evaluate(self, market):

        price = market.get("price", 0)
        volume = market.get("volume", 0)

        if volume < self.min_volume:
            return False

        if price < self.min_price or price > self.max_price:
            return False

        # Dedup — skip si évalué récemment
        market_name = market.get("market", "")
        now = time.time()

        if market_name in self.recently_seen:
            if now - self.recently_seen[market_name] < self.cooldown:
                return False

        self.recently_seen[market_name] = now
        return True

    def cleanup(self):
        """Purge les entrées expirées."""

        now = time.time()
        expired = [k for k, v in self.recently_seen.items() if now - v > self.cooldown * 2]
        for k in expired:
            del self.recently_seen[k]


# ============================================
# ULTRA FAST ORCHESTRATOR
# ============================================

class UltraFastOrchestrator:
    """Orchestrator multi-thread basse latence."""

    def __init__(self):

        print("\n" + "=" * 60)
        print("  ULTRA FAST TRADING BOT ALPHA")
        print(f"  Mode: {CONFIG['MODE']}")
        print(f"  Scan delay: {SCAN_DELAY * 1000}ms")
        print(f"  Queue size: {MAX_QUEUE_SIZE}")
        print("=" * 60)

        # Logger
        self.log = setup_logger("ultra_fast")
        self.log.info("Initializing Ultra Fast System...")

        # Database
        self.db = DatabaseManager(CONFIG["DB_PATH"])

        # Error handler
        self.errors = ErrorHandler(logger=self.log, db=self.db)

        # Market
        self.reader = PolymarketReader()
        self.scanner = AdaptiveScanner(config=CONFIG)
        self.filter = FastFilter()

        # AI ensemble
        self.ai_clients = [SecureAIClient(CONFIG) for _ in range(len(AI_MODELS))]
        self.confidence = ConfidenceManager(CONFIG)
        self.optimizer = ProfitOptimizer()

        # Execution
        self.execution = ExecutionEngine()
        self.cost_calc = CostCalculator(CONFIG)

        # Risk & Protection
        self.risk = RiskEngineV2(CONFIG)
        self.kill_switch = KillSwitch()

        # Queue
        self.market_queue = queue.Queue(MAX_QUEUE_SIZE)

        # State (thread-safe)
        self.lock = threading.Lock()
        self.capital = CONFIG["STARTING_CAPITAL"]
        self.starting_capital = CONFIG["STARTING_CAPITAL"]
        self.total_pnl = 0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0

        # Counters
        self.scan_count = 0
        self.filter_passed = 0
        self.filter_rejected = 0
        self.decisions_made = 0

        # Control
        self.running = True

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

        self.log.info("Ultra Fast System initialized.")

    # ============================================
    # THREAD 1 — MARKET SCANNER
    # ============================================

    def scanner_loop(self):
        """Scan continu Polymarket -> queue."""

        self.log.info("Scanner thread started")

        while self.running:

            try:
                start = time.time()

                markets = self.reader.get_markets()
                self.scan_count += 1

                if not markets:
                    self.scanner.record_scan(0)
                    time.sleep(SCAN_DELAY * 10)
                    continue

                self.scanner.record_scan(len(markets))

                # Sort by volume (best first)
                markets.sort(key=lambda x: x.get("volume", 0), reverse=True)

                pushed = 0
                for market in markets:

                    if not self.running:
                        break

                    if self.filter.evaluate(market):
                        self.filter_passed += 1

                        if not self.market_queue.full():
                            self.market_queue.put_nowait(market)
                            pushed += 1
                    else:
                        self.filter_rejected += 1

                elapsed = round((time.time() - start) * 1000, 1)
                self.log.debug(f"Scan #{self.scan_count}: {len(markets)} markets, {pushed} queued ({elapsed}ms)")

                # Cleanup filter cache periodically
                if self.scan_count % 100 == 0:
                    self.filter.cleanup()

                time.sleep(SCAN_DELAY)

            except Exception as e:
                self.errors.handle(e, "scanner_loop")
                self.scanner.record_error()
                time.sleep(1)

    # ============================================
    # THREAD 2 — DECISION ENGINE
    # ============================================

    def decision_loop(self):
        """Consume queue -> AI -> Risk -> Execute."""

        self.log.info("Decision engine started")

        while self.running:

            try:
                # Wait for market (timeout pour permettre shutdown)
                try:
                    market = self.market_queue.get(timeout=1)
                except queue.Empty:
                    continue

                self.decisions_made += 1

                # Error handler check
                if not self.errors.is_system_healthy():
                    self.log.critical("System unhealthy — skipping")
                    continue

                # Kill switch
                with self.lock:
                    current_capital = self.capital

                if not self.kill_switch.validate(current_capital, self.starting_capital):
                    self.log.critical(f"KILL SWITCH — capital: {current_capital}")
                    self.db.log_audit("KILL_SWITCH", f"capital={current_capital}")
                    self.running = False
                    break

                # AI evaluation (ensemble — fastest model wins)
                decision = self._evaluate_market(market)

                if decision is None:
                    continue

                # Confidence check
                conf_ok, conf_reason = self.confidence.validate(decision)
                if not conf_ok:
                    continue

                # Calculate size
                size = self.optimizer.calculate_size(current_capital, decision["confidence"])
                decision["size"] = size

                # Cost check
                cost_ok, cost_info = self.cost_calc.validate(decision)
                if not cost_ok:
                    continue

                # Risk check
                risk_ok, risk_reason = self.risk.validate_trade(
                    current_capital, size, decision["confidence"]
                )
                if not risk_ok:
                    self.log.risk(f"Blocked: {risk_reason}")
                    self.db.log_audit("RISK_BLOCKED", risk_reason)
                    continue

                # EXECUTE
                order = self.errors.safe_execute(
                    self.execution.execute, decision,
                    default=None, context="execution"
                )

                if order is None:
                    continue

                pnl = order.get("pnl", 0)

                # Update state (thread-safe)
                with self.lock:
                    self.capital += pnl
                    self.total_pnl += pnl
                    self.total_trades += 1

                    if pnl > 0:
                        self.wins += 1
                    else:
                        self.losses += 1

                self.risk.record_trade(pnl)
                self.risk.update_capital(self.capital)
                self.confidence.record_outcome(decision["confidence"], pnl > 0)

                # DB record
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

                self.log.trade(
                    decision["market"], decision["side"],
                    size, pnl, decision["confidence"]
                )
                self.log.info(f"PnL: {round(pnl, 2)} | Capital: {round(self.capital, 2)}")

            except Exception as e:
                self.errors.handle(e, "decision_loop")

    def _evaluate_market(self, market):
        """Évalue un marché via l'ensemble IA."""

        results = []
        for client, model in zip(self.ai_clients, AI_MODELS):
            result = self.errors.safe_execute(
                client.evaluate, market, model,
                default={"trade": False, "side": "NO", "confidence": 0},
                context=f"ai_{model}"
            )
            results.append(result)

        trades = [r for r in results if r.get("trade", False)]

        if not trades:
            return None

        best = max(trades, key=lambda x: x.get("confidence", 0))

        return {
            "market": market["market"],
            "token_id": market.get("token_id"),
            "side": best["side"],
            "confidence": best["confidence"],
            "price": market["price"],
            "volume": market.get("volume", 0),
            "model": best.get("model", ""),
            "source": best.get("source", "ai"),
        }

    def _save_state(self):

        with self.lock:
            self.db.save_state(
                capital=round(self.capital, 2),
                starting_capital=self.starting_capital,
                total_pnl=round(self.total_pnl, 2),
                total_trades=self.total_trades,
                wins=self.wins,
                losses=self.losses,
            )

    # ============================================
    # REPORT
    # ============================================

    def report(self):

        with self.lock:
            capital = self.capital
            pnl = self.total_pnl
            trades = self.total_trades
            wins = self.wins
            losses = self.losses

        winrate = round(wins / max(1, trades) * 100, 1)
        drawdown = round(
            (self.starting_capital - capital) / max(1, self.starting_capital) * 100, 2
        )

        self.log.info("=" * 50)
        self.log.info("ULTRA FAST REPORT")
        self.log.info(f"  Capital: {round(capital, 2)} (started: {self.starting_capital})")
        self.log.info(f"  Total PnL: {round(pnl, 2)}")
        self.log.info(f"  Trades: {trades} (W:{wins} L:{losses})")
        self.log.info(f"  Winrate: {winrate}%")
        self.log.info(f"  Drawdown: {drawdown}%")
        self.log.info(f"  Scans: {self.scan_count} | Filter: {self.filter_passed} passed, {self.filter_rejected} rejected")
        self.log.info(f"  Queue: {self.market_queue.qsize()} pending")

        # AI benchmark
        for client, model in zip(self.ai_clients, AI_MODELS):
            bench = client.get_benchmark()
            self.log.info(f"  AI [{model}]: {bench['success_rate']}% success, {bench['avg_latency']}s avg")

        # Risk
        risk_status = self.risk.get_status()
        self.log.info(f"  Risk: streak:{risk_status['loss_streak']} daily:{risk_status['daily_trades']} hourly:{risk_status['hourly_trades']}")

        # Scanner
        scan_status = self.scanner.get_status()
        self.log.info(f"  Scanner: interval:{scan_status['interval']}s rate_limited:{scan_status['rate_limited']}")

        # Errors
        err_status = self.errors.get_status()
        self.log.info(f"  Errors: {err_status['total_errors']} total, {err_status['critical_errors']} critical")

        self.log.info("=" * 50)

    # ============================================
    # START / STOP
    # ============================================

    def start(self):
        """Lance le système ultra rapide."""

        self.log.info("Starting Ultra Fast Trading System...")

        scanner_thread = threading.Thread(
            target=self.scanner_loop,
            name="scanner",
            daemon=True
        )

        decision_thread = threading.Thread(
            target=self.decision_loop,
            name="decision",
            daemon=True
        )

        scanner_thread.start()
        decision_thread.start()

        self.log.info("All threads running.")
        self.db.log_audit("SYSTEM_START", "Ultra Fast mode")

        last_report = time.time()
        last_backup = time.time()

        try:
            while self.running:
                time.sleep(1)

                now = time.time()

                # Periodic report
                if now - last_report >= REPORT_INTERVAL:
                    self.report()
                    last_report = now

                # Periodic backup
                if now - last_backup >= BACKUP_INTERVAL:
                    self.db.backup()
                    last_backup = now

                # Health check
                if not self.errors.is_system_healthy():
                    self.log.critical("System unhealthy — shutting down")
                    break

        except KeyboardInterrupt:
            print("\n\n  System stopped by user")

        self.shutdown()

    def shutdown(self):
        """Arrêt propre."""

        self.log.info("Shutting down Ultra Fast System...")
        self.running = False
        time.sleep(1)

        self.report()
        self._save_state()
        self.db.backup()
        self.db.log_audit("SYSTEM_STOP", "Ultra Fast shutdown")
        self.db.close()
        self.log.info("Shutdown complete.")


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":

    system = UltraFastOrchestrator()
    system.start()
