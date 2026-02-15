class ConfidenceManager:
    """Filtre décisions IA par confidence — empêche trades faibles."""

    def __init__(self, config):

        self.threshold = config["CONFIDENCE_THRESHOLD"]
        self.outcomes = []

    def should_trade(self, confidence):
        """Retourne True si la confidence justifie un trade."""

        if not isinstance(confidence, (int, float)):
            return False

        if confidence < 0 or confidence > 1:
            return False

        return confidence >= self.threshold

    def get_threshold(self):
        """Retourne le seuil actuel."""

        return self.threshold

    def record_outcome(self, confidence, won):
        """Enregistre le résultat d'un trade pour ajustement futur."""

        self.outcomes.append({
            "confidence": confidence,
            "won": won,
        })

        # Auto-ajustement tous les 50 trades
        if len(self.outcomes) >= 50:
            self._auto_adjust()

    def validate(self, decision):
        """Valide la confidence d'une décision. Retourne (ok, reason)."""

        if decision is None:
            return False, "no decision"

        confidence = decision.get("confidence", 0)

        if not self.should_trade(confidence):
            return False, f"confidence {confidence} < threshold {self.threshold}"

        return True, f"confidence {confidence} OK"

    def _auto_adjust(self):
        """Ajuste le seuil en fonction des résultats récents."""

        recent = self.outcomes[-50:]
        wins = [o for o in recent if o["won"]]
        winrate = len(wins) / len(recent)

        if winrate < 0.45:
            self.threshold = min(0.90, self.threshold + 0.05)
        elif winrate > 0.65:
            self.threshold = max(0.55, self.threshold - 0.02)
