import json
import os


class StateManager:

    def __init__(self, data_dir="alpha_system/data"):
        os.makedirs(data_dir, exist_ok=True)
        self.file = os.path.join(data_dir, "system_state.json")

    def save(self, state):

        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"  StateManager save error: {e}")

    def load(self):

        if not os.path.exists(self.file):
            return None

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
