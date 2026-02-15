import time


class AdaptiveScanner:
    """Contrôle la fréquence de scan — évite rate limit."""

    def __init__(self, base_interval=60):

        self.base_interval = base_interval
        self.current_interval = base_interval
        self.last_scan = 0
        self.consecutive_empty = 0
        self.consecutive_errors = 0

    def can_scan(self):
        """Vérifie si on peut scanner maintenant."""

        elapsed = time.time() - self.last_scan
        return elapsed >= self.current_interval

    def record_scan(self, market_count):
        """Enregistre le résultat d'un scan."""

        self.last_scan = time.time()

        if market_count == 0:
            self.consecutive_empty += 1
            # Ralentir si pas de marchés
            self.current_interval = min(
                self.base_interval * 5,
                self.current_interval * 1.5
            )
        else:
            self.consecutive_empty = 0
            self.consecutive_errors = 0
            self.current_interval = self.base_interval

    def record_error(self):
        """Enregistre une erreur de scan."""

        self.consecutive_errors += 1
        # Backoff exponentiel
        self.current_interval = min(
            self.base_interval * 10,
            self.current_interval * 2
        )

    def wait(self):
        """Attend l'intervalle courant."""

        time.sleep(self.current_interval)

    def get_status(self):

        return {
            "interval": round(self.current_interval, 1),
            "empty_streaks": self.consecutive_empty,
            "error_streaks": self.consecutive_errors,
        }
