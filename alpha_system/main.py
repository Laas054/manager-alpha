import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpha_system.config import CONFIG
from alpha_system.orchestrator import AlphaOrchestrator


def main():

    print("=" * 60)
    print("  TRADING BOT ALPHA v1.0")
    print(f"  Mode: {CONFIG['MODE']}")
    print(f"  Capital: {CONFIG['STARTING_CAPITAL']}")
    print(f"  Max trade: {CONFIG['MAX_TRADE_SIZE']}")
    print(f"  Confidence: {CONFIG['CONFIDENCE_THRESHOLD']}")
    print(f"  Max drawdown: {CONFIG['MAX_DRAWDOWN_PCT']*100}%")
    print(f"  Scan interval: {CONFIG['SCAN_INTERVAL']}s")
    print("=" * 60)

    bot = AlphaOrchestrator()

    cycle_count = 0

    while True:

        try:
            cycle_count += 1

            print(f"\n{'='*50}")
            print(f"  Cycle {cycle_count}")
            print(f"{'='*50}")

            result = bot.cycle()

            print(f"  -> {result}")

            # Report every 10 cycles
            if cycle_count % 10 == 0:
                bot.report()

            # DB backup every 100 cycles
            if cycle_count % 100 == 0:
                bot.db.backup()

            bot.scanner.wait()

        except KeyboardInterrupt:

            print("\n\n  System stopped by user")
            bot.report()
            bot.shutdown()
            break

        except Exception as e:

            print(f"\n  Fatal error: {e}")
            bot.errors.handle(e, "main_loop")
            time.sleep(CONFIG["SCAN_INTERVAL"])


if __name__ == "__main__":
    main()
