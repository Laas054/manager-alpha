class AgentSelector:
    """Sélectionne le meilleur résultat parmi plusieurs agents IA."""

    def __init__(self, min_confidence=0.70):

        self.min_confidence = min_confidence

        print(f"AgentSelector initialized (min_confidence: {min_confidence})")


    def select(self, results):
        """Retourne la meilleure décision ou None."""

        # Filtrer les TRADE uniquement
        trades = [r for r in results if r.get("decision") == "TRADE"]

        if not trades:
            return None

        # Sélectionner la plus haute confidence
        best = max(trades, key=lambda x: x.get("confidence", 0))

        if best.get("confidence", 0) < self.min_confidence:
            return None

        return best
