from alpha_system.ai.agent_brain import AgentBrain


class EnsembleEngine:

    def __init__(self):
        self.agents = [
            AgentBrain("deepseek-v3.2"),
            AgentBrain("qwen3-next:80b"),
            AgentBrain("glm-5"),
        ]

    def evaluate(self, market):

        print(f"\n=== ENSEMBLE ENGINE ===")
        print(f"Market: {market['market']}")

        results = []
        for agent in self.agents:
            result = agent.evaluate(market)
            results.append(result)
            trade = result.get("trade", False)
            conf = result.get("confidence", 0)
            side = result.get("side", "?")
            print(f"  [{agent.model}] trade:{trade} confidence:{conf} side:{side}")

        # Filtrer les TRADE
        trades = [r for r in results if r.get("trade", False)]

        if not trades:
            print("  Ensemble verdict: REJECT")
            return None

        # Meilleure confiance
        best = max(trades, key=lambda x: x.get("confidence", 0))

        if best.get("confidence", 0) < 0.65:
            print("  Ensemble verdict: REJECT (low confidence)")
            return None

        decision = {
            "market": market["market"],
            "token_id": market.get("token_id"),
            "side": best["side"],
            "confidence": best["confidence"],
            "price": market["price"],
            "volume": market.get("volume", 0),
        }

        print(f"  Ensemble verdict: TRADE confidence:{decision['confidence']} side:{decision['side']}")
        return decision
