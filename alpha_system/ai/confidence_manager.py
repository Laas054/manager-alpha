class ConfidenceManager:
    """Filtre les décisions IA par confidence — empêche trades faibles."""

    def __init__(self, config):

        self.threshold = config["CONFIDENCE_THRESHOLD"]

    def validate(self, decision):
        """Valide la confidence d'une décision. Retourne (ok, reason)."""

        if decision is None:
            return False, "no decision"

        confidence = decision.get("confidence", 0)

        if not isinstance(confidence, (int, float)):
            return False, "invalid confidence type"

        if confidence < 0 or confidence > 1:
            return False, f"confidence out of range: {confidence}"

        if confidence < self.threshold:
            return False, f"confidence {confidence} < threshold {self.threshold}"

        return True, f"confidence {confidence} OK"

    def adjust_threshold(self, recent_winrate):
        """Ajuste le seuil en fonction de la performance récente."""

        if recent_winrate < 0.45:
            self.threshold = min(0.90, self.threshold + 0.05)
        elif recent_winrate > 0.65:
            self.threshold = max(0.55, self.threshold - 0.02)
