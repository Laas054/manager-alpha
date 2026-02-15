class LiveSafetyController:

    def __init__(self):
        self.loss_streak = 0

    def record(self, pnl):
        if pnl < 0:
            self.loss_streak += 1
        else:
            self.loss_streak = 0

    def validate(self):
        return self.loss_streak < 5
