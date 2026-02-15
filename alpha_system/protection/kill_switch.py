from alpha_system.config import CONFIG


class KillSwitch:

    def __init__(self):
        self.max_drawdown = CONFIG["MAX_DRAWDOWN_PCT"]
        self.active = True

    def validate(self, capital, starting_capital):

        if not self.active:
            return False

        if starting_capital <= 0:
            return True

        drawdown = (starting_capital - capital) / starting_capital

        if drawdown > self.max_drawdown:
            print(f"\n  !!! KILL SWITCH !!! Drawdown: {round(drawdown*100,2)}%")
            self.active = False
            return False

        return True
