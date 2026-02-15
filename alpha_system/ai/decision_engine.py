from alpha_system.ai.ollama_client import OllamaClient
from alpha_system.ai.ai_engine import AIEngine


class AIDecisionEngine:

    def __init__(self):

        self.ai = OllamaClient()
        self.engine = AIEngine()

        print("AIDecisionEngine initialized")


    def decide(self, market_data):

        print("\n=== AI DECISION ENGINE ===")
        print(f"Market: {market_data['market']}")
        print(f"Price: {market_data['price']}")

        # analyse locale (rapide)
        local_decision = self.engine.evaluate(market_data)

        if local_decision is None:
            print("Local analysis: REJECT")
            return None

        # analyse IA (si disponible)
        ai_result = self.ai.evaluate_market(market_data)

        ai_decision = ai_result.get("decision", "REJECT")
        ai_confidence = ai_result.get("confidence", 0)
        ai_reason = ai_result.get("reason", "")

        print(f"AI decision: {ai_decision}")
        print(f"AI confidence: {ai_confidence}")
        print(f"AI reason: {ai_reason}")

        if ai_decision == "REJECT":
            print("AI REJECTED trade")
            return None

        # utiliser le side de l'IA si disponible
        if ai_result.get("side"):
            local_decision["side"] = ai_result["side"]

        # pondérer la confidence
        combined_confidence = (local_decision["confidence"] + ai_confidence) / 2
        local_decision["confidence"] = round(combined_confidence, 2)
        local_decision["size"] = self.engine.calculate_size(combined_confidence)
        local_decision["ai_reason"] = ai_reason

        print(f"Combined confidence: {combined_confidence}")
        print("Decision: TRADE")

        return local_decision
