class DrawdownProtection:

    def __init__(self, max_drawdown=0.20):

        self.max_drawdown = max_drawdown
        self.peak_capital = 0

        print("DrawdownProtection initialized")


    def update(self, current_capital):

        if current_capital > self.peak_capital:
            self.peak_capital = current_capital


    def check(self, current_capital):

        if self.peak_capital == 0:
            return True

        drawdown = (self.peak_capital - current_capital) / self.peak_capital

        if drawdown > self.max_drawdown:

            print(f"\nDRAWDOWN ALERT: {round(drawdown * 100, 2)}%")
            return False

        return True
