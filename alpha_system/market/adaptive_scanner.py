import time


class AdaptiveScanner:
    """Contrôle la fréquence de scan — évite rate limit.
    get_interval(), report_rate_limit(), clear_rate_limit()."""

    def __init__(self, config=None, base_interval=60):

        # Config-driven si disponible
        if config:
            self.base_interval = config.get("SCAN_INTERVAL", base_interval)
            self.min_interval = config.get("MIN_SCAN_INTERVAL", 15)
            self.max_interval = config.get("MAX_SCAN_INTERVAL", 120)
        else:
            self.base_interval = base_interval
            self.min_interval = 15
            self.max_interval = 120

        self.current_interval = self.base_interval
        self.last_scan = 0
        self.consecutive_empty = 0
        self.consecutive_errors = 0

        # Rate limit tracking
        self.rate_limited = False
        self.rate_limit_count = 0
        self.rate_limit_until = 0

    def can_scan(self):
        """Vérifie si on peut scanner maintenant."""

        # Rate limit actif ?
        if self.rate_limited and time.time() < self.rate_limit_until:
            return False

        elapsed = time.time() - self.last_scan
        return elapsed >= self.current_interval

    def record_scan(self, market_count):
        """Enregistre le résultat d'un scan."""

        self.last_scan = time.time()

        if market_count == 0:
            self.consecutive_empty += 1
            # Ralentir si pas de marchés
            self.current_interval = min(
                self.max_interval,
                self.current_interval * 1.5
            )
        else:
            self.consecutive_empty = 0
            self.consecutive_errors = 0
            self.current_interval = self.base_interval

    def record_error(self):
        """Enregistre une erreur de scan."""

        self.consecutive_errors += 1
        # Backoff exponentiel (respecte max_interval)
        self.current_interval = min(
            self.max_interval * 2,
            self.current_interval * 2
        )

    # === DIRECTIVE METHODS ===

    def get_interval(self):
        """Retourne l'intervalle de scan actuel (secondes)."""

        return round(self.current_interval, 1)

    def report_rate_limit(self, wait_seconds=60):
        """Signale un rate limit — augmente l'intervalle et bloque temporairement."""

        self.rate_limited = True
        self.rate_limit_count += 1
        self.rate_limit_until = time.time() + wait_seconds

        # Augmenter l'intervalle (backoff)
        self.current_interval = min(
            self.max_interval * 2,
            self.current_interval * 2
        )

    def clear_rate_limit(self):
        """Efface le rate limit — restaure l'intervalle normal."""

        self.rate_limited = False
        self.rate_limit_until = 0
        self.current_interval = max(self.min_interval, self.base_interval)

    def set_interval(self, seconds):
        """Force un intervalle (respecte min/max)."""

        self.current_interval = max(
            self.min_interval,
            min(self.max_interval, seconds)
        )

    def wait(self):
        """Attend l'intervalle courant."""

        time.sleep(self.current_interval)

    def get_status(self):

        return {
            "interval": round(self.current_interval, 1),
            "min_interval": self.min_interval,
            "max_interval": self.max_interval,
            "empty_streaks": self.consecutive_empty,
            "error_streaks": self.consecutive_errors,
            "rate_limited": self.rate_limited,
            "rate_limit_count": self.rate_limit_count,
        }
