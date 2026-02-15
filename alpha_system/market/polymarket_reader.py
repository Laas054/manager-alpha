import json
import requests


class PolymarketReader:

    def __init__(self):
        self.url = "https://gamma-api.polymarket.com/markets"

    def get_markets(self):
        try:
            response = requests.get(
                self.url,
                params={"closed": "false", "active": "true", "limit": 100},
                timeout=15
            )
            data = response.json()
        except Exception as e:
            print(f"  PolymarketReader error: {e}")
            return []

        markets = []
        for m in data:
            try:
                # outcomePrices = JSON string "[\"0.78\", \"0.22\"]"
                prices_raw = m.get("outcomePrices", "[]")
                if isinstance(prices_raw, str):
                    prices = json.loads(prices_raw)
                else:
                    prices = prices_raw

                if not prices or len(prices) < 1 or prices[0] is None:
                    continue

                price = float(prices[0])

                # clobTokenIds = JSON string
                tokens_raw = m.get("clobTokenIds", "[]")
                if isinstance(tokens_raw, str):
                    tokens = json.loads(tokens_raw)
                else:
                    tokens = tokens_raw

                token_id = tokens[0] if tokens else None
                volume = float(m.get("volume", 0) or 0)

                if not m.get("active", True):
                    continue

                markets.append({
                    "market": m.get("question", "Unknown"),
                    "price": price,
                    "token_id": token_id,
                    "volume": volume,
                })
            except Exception:
                continue

        return markets
