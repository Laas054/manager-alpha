class DrawdownGuard:
    """Protection contre le drawdown progressif."""

    def __init__(self, warning_threshold=0.10, halt_threshold=0.15):

        self.warning = warning_threshold
        self.halt = halt_threshold

        print(f"DrawdownGuard initialized (warn:{warning_threshold*100}% halt:{halt_threshold*100}%)")


    def check(self, state):

        dd = state.get_drawdown()

        if dd > self.halt:
            print(f"\n  DRAWDOWN HALT: {round(dd*100,2)}% — reducing position sizes")
            return "HALT"

        if dd > self.warning:
            print(f"\n  DRAWDOWN WARNING: {round(dd*100,2)}%")
            return "WARNING"

        return "OK"


    def size_multiplier(self, state):
        """Réduit la taille des positions en fonction du drawdown."""

        dd = state.get_drawdown()

        if dd > self.halt:
            return 0.25
        if dd > self.warning:
            return 0.50
        return 1.0
