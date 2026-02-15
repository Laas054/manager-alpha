class StrategyEngine:

    def __init__(self):

        self.min_edge = 0.05
        self.min_confidence = 0.60

        print("StrategyEngine initialized")


    def evaluate_market(self, market_data):

        print("\n=== STRATEGY ENGINE ===")

        price = market_data["price"]

        confidence = self.calculate_confidence(price)

        edge = self.calculate_edge(price)


        print("Price:", price)
        print("Confidence:", confidence)
        print("Edge:", edge)


        if confidence < self.min_confidence:

            print("Rejected: low confidence")
            return None


        if edge < self.min_edge:

            print("Rejected: low edge")
            return None


        side = self.select_side(price)

        size = self.calculate_size(confidence)


        return {

            "market": market_data["market"],
            "token_id": market_data.get("token_id"),
            "side": side,
            "price": price,
            "size": size,
            "confidence": confidence,
            "edge": edge

        }


    def calculate_confidence(self, price):

        distance = abs(price - 0.5)

        confidence = distance * 2

        return round(confidence, 2)


    def calculate_edge(self, price):

        return abs(price - 0.5)


    def select_side(self, price):

        if price > 0.5:
            return "YES"
        else:
            return "NO"


    def calculate_size(self, confidence):

        base_size = 10

        return int(base_size * confidence)
