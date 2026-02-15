"""
WebSocket Orchestrator — Réception instantanée des prix Polymarket.

Au lieu de scan HTTP (100-500ms), les updates arrivent en push (1-20ms).
Pipeline: WebSocket -> FastFilter -> AI -> Risk -> Execute

Latence cible: 15-60ms
"""

import threading
import json
import time
import websocket
from datetime import datetime, timezone

from alpha_system.config import CONFIG
from alpha_system.utils.logger import setup_logger
from alpha_system.memory.database import DatabaseManager
from alpha_system.protection.error_handler import ErrorHandler
from alpha_system.protection.kill_switch import KillSwitch
from alpha_system.ai.secure_ai_client import SecureAIClient
from alpha_system.ai.confidence_manager import ConfidenceManager
from alpha_system.ai.profit_optimizer import ProfitOptimizer
from alpha_system.execution.execution_engine import ExecutionEngine
from alpha_system.execution.cost_calculator import CostCalculator
from alpha_system.risk.risk_engine_v2 import RiskEngineV2


# ============================================
# CONFIG
# ============================================

POLYMARKET_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
AI_MODELS = ["deepseek-v3.2", "qwen3-next:80b", "glm-5"]
REPORT_INTERVAL = 60
BACKUP_INTERVAL = 600
RECONNECT_DELAY = 5


# ============================================
# FAST FILTER
# ============================================

class FastFilter:
    """Filtre instantané pre-AI."""

    def __init__(self):
        self.min_volume = 1000
        self.min_price = 0.05
        self.max_price = 0.95
        self.recently_seen = {}
        self.cooldown = 60  # 60s entre réévaluations du même marché

    def evaluate(self, market):

        price = market.get("price", 0)
        volume = market.get("volume", 0)

        if volume < self.min_volume:
            return False

        if price < self.min_price or price > self.max_price:
            return False

        market_name = market.get("market", "")
        now = time.time()

        if market_name in self.recently_seen:
            if now - self.recently_seen[market_name] < self.cooldown:
                return False

        self.recently_seen[market_name] = now
        return True

    def cleanup(self):
        now = time.time()
        expired = [k for k, v in self.recently_seen.items() if now - v > self.cooldown * 2]
        for k in expired:
            del self.recently_seen[k]


# ============================================
# WEBSOCKET ORCHESTRATOR
# ============================================

class WebSocketOrchestrator:
    """Orchestrator WebSocket — push-based, ultra basse latence."""

    def __init__(self):

        print("\n" + "=" * 60)
        print("  WEBSOCKET TRADING BOT ALPHA")
        print(f"  Mode: {CONFIG['MODE']}")
        print(f"  WS URL: {POLYMARKET_WS_URL}")
        print("=" * 60)

        # Logger
        self.log = setup_logger("websocket_bot")
        self.log.info("Initializing WebSocket System...")

        # Database
        self.db = DatabaseManager(CONFIG["DB_PATH"])

        # Error handler
        self.errors = ErrorHandler(logger=self.log, db=self.db)

        # Filter
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

        # State (thread-safe)
        self.lock = threading.Lock()
        self.capital = CONFIG["STARTING_CAPITAL"]
        self.starting_capital = CONFIG["STARTING_CAPITAL"]
        self.total_pnl = 0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0

        # Counters
        self.messages_received = 0
        self.filter_passed = 0
        self.filter_rejected = 0

        # Control
        self.running = True
        self.ws = None

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

        self.log.info("WebSocket System initialized.")

    # ============================================
    # WEBSOCKET HANDLERS
    # ============================================

    def on_open(self, ws):
        """Connexion établie — subscribe aux marchés."""

        self.log.info("WebSocket connected")
        self.db.log_audit("WS_CONNECTED", POLYMARKET_WS_URL)

        # Subscribe to market updates
        subscribe_msg = json.dumps({
            "type": "subscribe",
            "channel": "market",
        })
        ws.send(subscribe_msg)
        self.log.info("Subscribed to market channel")

    def on_message(self, ws, message):
        """Message reçu — pipeline instantané."""

        self.messages_received += 1

        try:
            data = json.loads(message)

            # Extraire les données marché
            market = self._parse_ws_message(data)

            if market is None:
                return

            # FAST FILTER (~1ms)
            if not self.filter.evaluate(market):
                self.filter_rejected += 1
                return

            self.filter_passed += 1

            # Vérifier santé système
            if not self.errors.is_system_healthy():
                return

            with self.lock:
                current_capital = self.capital

            if not self.kill_switch.validate(current_capital, self.starting_capital):
                self.log.critical(f"KILL SWITCH — capital: {current_capital}")
                self.running = False
                return

            # AI EVALUATION (ensemble)
            decision = self._evaluate_market(market)

            if decision is None:
                return

            # CONFIDENCE CHECK
            conf_ok, _ = self.confidence.validate(decision)
            if not conf_ok:
                return

            # SIZE
            size = self.optimizer.calculate_size(current_capital, decision["confidence"])
            decision["size"] = size

            # COST CHECK
            cost_ok, _ = self.cost_calc.validate(decision)
            if not cost_ok:
                return

            # RISK CHECK
            risk_ok, risk_reason = self.risk.validate_trade(
                current_capital, size, decision["confidence"]
            )
            if not risk_ok:
                self.log.risk(f"Blocked: {risk_reason}")
                return

            # EXECUTE INSTANTLY
            order = self.errors.safe_execute(
                self.execution.execute, decision,
                default=None, context="ws_execution"
            )

            if order is None:
                return

            pnl = order.get("pnl", 0)

            # UPDATE STATE
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

            # DB
            self.db.record_trade(
                market=decision["market"],
                side=decision["side"],
                price=decision["price"],
                size=size,
                pnl=pnl,
                confidence=decision["confidence"],
                model=decision.get("model", ""),
                source="websocket",
                status=order.get("status", "SIMULATED"),
            )
            self._save_state()

            self.log.trade(
                decision["market"], decision["side"],
                size, pnl, decision["confidence"]
            )

        except Exception as e:
            self.errors.handle(e, "on_message")

    def on_error(self, ws, error):
        self.log.error(f"WebSocket error: {error}")
        self.errors.handle(error if isinstance(error, Exception) else Exception(str(error)), "websocket")

    def on_close(self, ws, close_status_code, close_msg):
        self.log.warning(f"WebSocket closed: {close_status_code} {close_msg}")

    # ============================================
    # PARSING
    # ============================================

    def _parse_ws_message(self, data):
        """Parse un message WebSocket Polymarket en format marché standard."""

        # Format attendu des WS Polymarket (peut varier)
        if isinstance(data, list):
            for item in data:
                parsed = self._parse_single(item)
                if parsed:
                    return parsed
            return None

        return self._parse_single(data)

    def _parse_single(self, data):
        """Parse un seul update marché."""

        if not isinstance(data, dict):
            return None

        # Chercher les champs prix dans différents formats possibles
        price = data.get("price") or data.get("best_ask") or data.get("last_trade_price")
        if price is None:
            return None

        try:
            price = float(price)
        except (ValueError, TypeError):
            return None

        market_name = data.get("market") or data.get("question") or data.get("asset_id", "unknown")
        volume = float(data.get("volume", 0) or 0)
        token_id = data.get("token_id") or data.get("asset_id")

        return {
            "market": str(market_name),
            "price": price,
            "volume": volume,
            "token_id": token_id,
        }

    # ============================================
    # AI EVALUATION
    # ============================================

    def _evaluate_market(self, market):
        """Évalue via ensemble IA."""

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
            "source": "websocket",
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

        winrate = round(wins / max(1, trades) * 100, 1)

        self.log.info("=" * 50)
        self.log.info("WEBSOCKET REPORT")
        self.log.info(f"  Capital: {round(capital, 2)}")
        self.log.info(f"  PnL: {round(pnl, 2)} | Trades: {trades} | Winrate: {winrate}%")
        self.log.info(f"  WS messages: {self.messages_received}")
        self.log.info(f"  Filter: {self.filter_passed} passed, {self.filter_rejected} rejected")

        for client, model in zip(self.ai_clients, AI_MODELS):
            bench = client.get_benchmark()
            self.log.info(f"  AI [{model}]: {bench['success_rate']}% success")

        risk_status = self.risk.get_status()
        self.log.info(f"  Risk: streak:{risk_status['loss_streak']} daily:{risk_status['daily_trades']}")

        err_status = self.errors.get_status()
        self.log.info(f"  Errors: {err_status['total_errors']} total")
        self.log.info("=" * 50)

    # ============================================
    # CONNECT WITH AUTO-RECONNECT
    # ============================================

    def _connect(self):
        """Connexion WebSocket avec auto-reconnect."""

        while self.running:
            try:
                self.log.info(f"Connecting to {POLYMARKET_WS_URL}...")

                self.ws = websocket.WebSocketApp(
                    POLYMARKET_WS_URL,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                )

                self.ws.run_forever(ping_interval=30, ping_timeout=10)

                if self.running:
                    self.log.warning(f"Reconnecting in {RECONNECT_DELAY}s...")
                    time.sleep(RECONNECT_DELAY)

            except Exception as e:
                self.errors.handle(e, "ws_connect")
                time.sleep(RECONNECT_DELAY)

    # ============================================
    # START / STOP
    # ============================================

    def start(self):
        """Lance le système WebSocket."""

        self.log.info("Starting WebSocket Trading System...")
        self.db.log_audit("SYSTEM_START", "WebSocket mode")

        ws_thread = threading.Thread(
            target=self._connect,
            name="websocket",
            daemon=True
        )
        ws_thread.start()

        last_report = time.time()
        last_backup = time.time()

        try:
            while self.running:
                time.sleep(1)

                now = time.time()

                if now - last_report >= REPORT_INTERVAL:
                    self.report()
                    self.filter.cleanup()
                    last_report = now

                if now - last_backup >= BACKUP_INTERVAL:
                    self.db.backup()
                    last_backup = now

                if not self.errors.is_system_healthy():
                    self.log.critical("System unhealthy — shutting down")
                    break

        except KeyboardInterrupt:
            print("\n\n  System stopped by user")

        self.shutdown()

    def shutdown(self):
        """Arrêt propre."""

        self.log.info("Shutting down WebSocket System...")
        self.running = False

        if self.ws:
            self.ws.close()

        time.sleep(1)
        self.report()
        self._save_state()
        self.db.backup()
        self.db.log_audit("SYSTEM_STOP", "WebSocket shutdown")
        self.db.close()
        self.log.info("Shutdown complete.")


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":

    system = WebSocketOrchestrator()
    system.start()
