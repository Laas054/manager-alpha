"""Monitoring live du bot Alpha AI Trading."""

import sys
import os
import time
import json
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def monitor(interval=10):
    """Affiche l'état du système en continu."""

    data_dir = "alpha_system/data"

    print("=" * 60)
    print("  ALPHA AI TRADING — MONITOR")
    print("=" * 60)

    while True:

        try:
            print(f"\n--- {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC ---")

            # State
            state_file = os.path.join(data_dir, "system_state.json")
            if os.path.exists(state_file):
                with open(state_file, "r") as f:
                    state = json.load(f)
                print(f"  Capital: {round(state['current_capital'], 2)}")
                print(f"  PnL: {round(state['total_pnl'], 2)}")
                print(f"  Trades: {state['total_trades']} (W:{state['wins']} L:{state['losses']})")
                winrate = round(state['wins'] / max(1, state['total_trades']) * 100, 1)
                print(f"  Winrate: {winrate}%")
                print(f"  Active: {state['active']}")
            else:
                print("  (no state file yet)")

            # Positions
            pos_file = os.path.join(data_dir, "positions.json")
            if os.path.exists(pos_file):
                with open(pos_file, "r") as f:
                    pos_data = json.load(f)
                positions = pos_data.get("positions", {})
                print(f"  Open positions: {len(positions)}")
                for m, p in positions.items():
                    print(f"    {m[:50]} | {p['side']} | size:{p['size']}")
            else:
                print("  (no positions file)")

            # Orders
            ord_file = os.path.join(data_dir, "orders.json")
            if os.path.exists(ord_file):
                with open(ord_file, "r") as f:
                    orders = json.load(f)
                open_orders = [o for o in orders.values() if o.get("status") == "OPEN"]
                print(f"  Total orders: {len(orders)} | Open: {len(open_orders)}")

            print(f"\n  Bot running safely")
            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            break

        except Exception as e:
            print(f"  Monitor error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    monitor(interval)
