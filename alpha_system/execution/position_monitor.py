"""
Position Monitor WebSocket — suivi temps réel des positions ouvertes.

Écoute les prix Polymarket via WebSocket, met à jour le PositionManager,
déclenche TP/SL/Trailing automatiquement. Compatible DRY et LIVE.

Latence: 1-20ms (vs 100-500ms HTTP polling)
"""

import asyncio
import json
import websockets
from datetime import datetime, UTC

from alpha_system.config import CONFIG
from alpha_system.utils.logger import setup_logger


# ============================================
# CONFIG
# ============================================

POLYMARKET_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
REFRESH_INTERVAL = 10     # secondes entre refresh subscriptions
RECONNECT_DELAY = 5       # secondes avant reconnexion


# ============================================
# POSITION MONITOR
# ============================================

class PositionMonitor:
    """Monitor temps réel des positions via WebSocket Polymarket.

    - Écoute les prix temps réel
    - Met à jour PositionManager
    - Déclenche TP / SL / Trailing automatiquement
    """

    def __init__(self, position_manager, websocket_url=None, logger=None, database=None):

        self.position_manager = position_manager
        self.websocket_url = websocket_url or POLYMARKET_WS_URL
        self.log = logger or setup_logger("position_monitor")
        self.database = database

        self.ws = None
        self.running = False
        self.subscribed_markets = set()

        # Stats
        self.messages_received = 0
        self.price_updates = 0
        self.exits_triggered = 0
        self.errors = 0
        self.connected = False

        self.log.info("PositionMonitor initialized")

    # ============================================
    # START MONITOR
    # ============================================

    async def start(self):
        """Connexion WebSocket avec auto-reconnect."""

        self.running = True
        self.log.info(f"Connecting to {self.websocket_url}...")

        while self.running:
            try:
                async with websockets.connect(
                    self.websocket_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=5,
                ) as websocket:

                    self.ws = websocket
                    self.connected = True
                    self.log.info("WebSocket connected")

                    if self.database:
                        self.database.log_audit("MONITOR_CONNECTED", self.websocket_url)

                    await self.subscribe_to_open_positions()
                    await self.listen()

            except asyncio.CancelledError:
                break

            except Exception as e:
                self.connected = False
                self.errors += 1
                self.log.error(f"WebSocket error: {e}")

                if self.running:
                    self.log.info(f"Reconnecting in {RECONNECT_DELAY}s...")
                    await asyncio.sleep(RECONNECT_DELAY)

    # ============================================
    # SUBSCRIBE TO OPEN POSITIONS
    # ============================================

    async def subscribe_to_open_positions(self):
        """Subscribe aux marchés de toutes les positions ouvertes."""

        open_positions = self.position_manager.get_open_positions()

        for market_id, position in open_positions.items():

            if market_id not in self.subscribed_markets:
                await self.subscribe_market(market_id, position.token_id)

        # Unsubscribe des positions fermées
        closed = self.subscribed_markets - set(open_positions.keys())
        for market_id in closed:
            self.subscribed_markets.discard(market_id)

    async def subscribe_market(self, market_id, token_id):
        """Subscribe à un marché spécifique."""

        if not self.ws or not token_id:
            return

        subscribe_msg = {
            "type": "subscribe",
            "channel": "price",
            "token_id": token_id,
        }

        try:
            await self.ws.send(json.dumps(subscribe_msg))
            self.subscribed_markets.add(market_id)
            self.log.debug(f"Subscribed to {market_id[:40]} ({token_id[:20]}...)")
        except Exception as e:
            self.log.error(f"Subscribe error: {e}")

    # ============================================
    # LISTEN LOOP
    # ============================================

    async def listen(self):
        """Boucle d'écoute WebSocket."""

        while self.running:
            try:
                message = await asyncio.wait_for(
                    self.ws.recv(),
                    timeout=60
                )

                self.messages_received += 1
                data = json.loads(message)
                await self.process_message(data)

            except asyncio.TimeoutError:
                # Pas de message depuis 60s — refresh subscriptions
                await self.subscribe_to_open_positions()

            except asyncio.CancelledError:
                break

            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                self.log.warning("WebSocket connection closed")
                break

            except Exception as e:
                self.errors += 1
                self.log.error(f"Listen error: {e}")

    # ============================================
    # PROCESS MESSAGE
    # ============================================

    async def process_message(self, data):
        """Traite un message WebSocket — update prix et vérifie exits."""

        # Supporter différents formats de message
        if isinstance(data, list):
            for item in data:
                await self._process_single(item)
        else:
            await self._process_single(data)

    async def _process_single(self, data):
        """Traite un seul update de prix."""

        if not isinstance(data, dict):
            return

        token_id = data.get("token_id") or data.get("asset_id")
        price = data.get("price") or data.get("best_ask") or data.get("last_trade_price")

        if token_id is None or price is None:
            return

        try:
            price = float(price)
        except (ValueError, TypeError):
            return

        # Trouver le market_id correspondant
        market_id = self._find_market_id(token_id)

        if market_id is None:
            return

        self.price_updates += 1

        # Update position — peut déclencher TP/SL/Trailing
        result = self.position_manager.update_price(market_id, price)

        if result is not None:
            # Une position a été fermée automatiquement
            self.exits_triggered += 1
            self.log.info(
                f"AUTO EXIT | {result['market_id'][:40]} | {result['reason']} "
                f"| PnL: {result['pnl']}"
            )

            if self.database:
                self.database.log_audit(
                    "AUTO_EXIT",
                    f"{result['reason']} pnl={result['pnl']}"
                )

    # ============================================
    # FIND MARKET ID
    # ============================================

    def _find_market_id(self, token_id):
        """Trouve le market_id à partir d'un token_id."""

        for market_id, position in self.position_manager.positions.items():
            if position.token_id == token_id:
                return market_id
        return None

    # ============================================
    # AUTO REFRESH SUBSCRIPTIONS
    # ============================================

    async def auto_refresh(self, interval=None):
        """Vérifie périodiquement les nouvelles positions ouvertes."""

        interval = interval or REFRESH_INTERVAL

        while self.running:
            try:
                if self.connected and self.ws:
                    await self.subscribe_to_open_positions()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log.error(f"Refresh error: {e}")
                await asyncio.sleep(interval)

    # ============================================
    # PERIODIC REPORT
    # ============================================

    async def periodic_report(self, interval=60):
        """Affiche un rapport périodique."""

        while self.running:
            try:
                await asyncio.sleep(interval)
                self.report()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def report(self):
        """Affiche le statut du monitor."""

        pos_status = self.position_manager.get_status()

        self.log.info("=" * 40)
        self.log.info("POSITION MONITOR REPORT")
        self.log.info(f"  Connected: {self.connected}")
        self.log.info(f"  Subscribed: {len(self.subscribed_markets)} markets")
        self.log.info(f"  Messages: {self.messages_received} | Price updates: {self.price_updates}")
        self.log.info(f"  Auto exits: {self.exits_triggered} | Errors: {self.errors}")
        self.log.info(f"  Open positions: {pos_status['open_count']}")
        self.log.info(f"  Unrealized PnL: {pos_status['unrealized_pnl']}")
        self.log.info(f"  Exposure: {pos_status['total_exposure']}")
        self.log.info("=" * 40)

    # ============================================
    # STOP
    # ============================================

    async def stop(self):
        """Arrêt propre du monitor."""

        self.log.info("Stopping PositionMonitor...")
        self.running = False

        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass

        self.connected = False
        self.report()
        self.log.info("PositionMonitor stopped")

    # ============================================
    # FULL START (asyncio.gather)
    # ============================================

    async def run(self):
        """Lance monitor + refresh + report en parallèle."""

        self.log.info("Starting PositionMonitor full system...")

        if self.database:
            self.database.log_audit("MONITOR_START", "PositionMonitor")

        try:
            await asyncio.gather(
                self.start(),
                self.auto_refresh(),
                self.periodic_report(),
            )
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    def get_status(self):
        """Retourne le statut complet."""

        return {
            "connected": self.connected,
            "subscribed_markets": len(self.subscribed_markets),
            "messages_received": self.messages_received,
            "price_updates": self.price_updates,
            "exits_triggered": self.exits_triggered,
            "errors": self.errors,
        }


# ============================================
# ENTRY POINT (standalone)
# ============================================

if __name__ == "__main__":

    from alpha_system.execution.position_manager import PositionManager
    from alpha_system.execution.execution_engine import ExecutionEngine
    from alpha_system.execution.cost_calculator import CostCalculator
    from alpha_system.risk.risk_engine_v2 import RiskEngineV2
    from alpha_system.memory.database import DatabaseManager

    log = setup_logger("monitor_standalone")
    db = DatabaseManager(CONFIG["DB_PATH"])
    risk = RiskEngineV2(CONFIG)
    cost = CostCalculator(CONFIG)
    execution = ExecutionEngine()

    pm = PositionManager(
        execution=execution,
        risk_engine=risk,
        database=db,
        cost_calc=cost,
        logger=log,
    )

    monitor = PositionMonitor(
        position_manager=pm,
        logger=log,
        database=db,
    )

    print("\nPosition Monitor — Standalone Mode")
    print("Press Ctrl+C to stop\n")

    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\nStopped by user")
