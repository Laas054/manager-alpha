import json
import os
from pathlib import Path


class StateManager:
    """Persistence de l'état système — sauvegarde/restauration après crash."""

    def __init__(self, data_dir="alpha_system/data"):

        os.makedirs(data_dir, exist_ok=True)
        self.file = os.path.join(data_dir, "system_state.json")

        print(f"StateManager initialized ({self.file})")


    def save(self, state):
        """Sauvegarde l'état complet du système."""

        data = {
            "starting_capital": state.starting_capital,
            "current_capital": state.current_capital,
            "total_pnl": state.total_pnl,
            "total_trades": state.total_trades,
            "wins": state.wins,
            "losses": state.losses,
            "daily_pnl": state.daily_pnl,
            "peak_capital": state.peak_capital,
            "active": state.active,
            "started_at": state.started_at,
        }

        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"  StateManager save error: {e}")


    def load(self):
        """Charge l'état sauvegardé. Retourne None si pas de fichier."""

        if not os.path.exists(self.file):
            return None

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  StateManager load error: {e}")
            return None


    def restore(self, state):
        """Restaure un SystemState depuis le fichier sauvegardé."""

        data = self.load()
        if not data:
            return False

        state.starting_capital = data["starting_capital"]
        state.current_capital = data["current_capital"]
        state.total_pnl = data["total_pnl"]
        state.total_trades = data["total_trades"]
        state.wins = data["wins"]
        state.losses = data["losses"]
        state.daily_pnl = data["daily_pnl"]
        state.peak_capital = data["peak_capital"]
        state.active = data["active"]
        state.started_at = data["started_at"]

        print(f"  State restored | Capital: {state.current_capital} | Trades: {state.total_trades}")
        return True
