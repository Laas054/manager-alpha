import time
from datetime import datetime, UTC


class Scheduler:
    """Gère les cycles et le timing du bot."""

    def __init__(self, interval=60):

        self.interval = interval
        self.cycle_count = 0

        print(f"Scheduler initialized (interval: {interval}s)")


    def next_cycle(self):

        self.cycle_count += 1
        return self.cycle_count


    def wait(self):

        print(f"\nSleeping {self.interval}s...")
        time.sleep(self.interval)


    def should_optimize(self, every_n=5):

        return self.cycle_count % every_n == 0


    def should_reset_daily(self):
        """Simplifié : reset toutes les 1440 minutes (24h en cycles de 60s)."""

        return self.cycle_count % 1440 == 0
