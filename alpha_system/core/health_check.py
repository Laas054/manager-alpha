import requests
from datetime import datetime, UTC


class HealthCheck:
    """Vérifie la santé de tous les composants avant chaque cycle."""

    def __init__(self):

        self.last_check = None
        self.status = {}

        print("HealthCheck initialized")


    def check(self, state=None, exposure=None):
        """Vérifie tous les composants. Retourne True si tout est OK."""

        self.last_check = datetime.now(UTC).isoformat()
        self.status = {}
        all_ok = True

        # 1. System state actif
        if state:
            self.status["state_active"] = state.active
            if not state.active:
                print("  [HEALTH] System state INACTIVE")
                all_ok = False

        # 2. Capital positif
        if state:
            self.status["capital_positive"] = state.current_capital > 0
            if state.current_capital <= 0:
                print("  [HEALTH] Capital <= 0")
                all_ok = False

        # 3. API Polymarket accessible
        try:
            r = requests.get(
                "https://gamma-api.polymarket.com/markets?limit=1",
                timeout=10
            )
            self.status["polymarket_api"] = r.status_code == 200
            if r.status_code != 200:
                print(f"  [HEALTH] Polymarket API: {r.status_code}")
                all_ok = False
        except Exception:
            self.status["polymarket_api"] = False
            print("  [HEALTH] Polymarket API unreachable")
            all_ok = False

        # 4. Exposure cohérente
        if exposure:
            self.status["exposure_ok"] = exposure.available >= 0
            if exposure.available < 0:
                print("  [HEALTH] Negative available capital in exposure")
                all_ok = False

        self.status["all_ok"] = all_ok
        return all_ok


    def report(self):

        print("\n=== HEALTH CHECK ===")
        for k, v in self.status.items():
            icon = "OK" if v else "FAIL"
            print(f"  {k}: {icon}")
