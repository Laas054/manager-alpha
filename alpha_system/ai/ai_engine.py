class AIEngine:

    def __init__(self):

        self.min_confidence = 0.60
        self.min_edge = 0.05

        print("AIEngine initialized")


    def calculate_confidence(self, price):

        distance = abs(price - 0.5)
        return round(distance * 2, 2)


    def calculate_edge(self, price):

        return round(abs(price - 0.5), 4)


    def select_side(self, price):

        return "YES" if price > 0.5 else "NO"


    def calculate_size(self, confidence, base_size=10):

        return max(1, int(base_size * confidence))


    def evaluate(self, market_data):

        price = market_data["price"]
        confidence = self.calculate_confidence(price)
        edge = self.calculate_edge(price)

        if confidence < self.min_confidence:
            return None

        if edge < self.min_edge:
            return None

        return {
            "market": market_data["market"],
            "token_id": market_data.get("token_id"),
            "side": self.select_side(price),
            "price": price,
            "size": self.calculate_size(confidence),
            "confidence": confidence,
            "edge": edge
        }
