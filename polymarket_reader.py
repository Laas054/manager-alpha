import json
import requests


class PolymarketReader:

    def __init__(self):

        self.url = "https://gamma-api.polymarket.com/markets"

        print("PolymarketReader initialized")


    def get_markets(self, limit=10):

        print("\nFetching Polymarket markets...")

        try:

            params = {"closed": "false", "limit": 100, "active": "true"}
            response = requests.get(self.url, params=params)

            markets = response.json()

            return markets[:limit]

        except Exception as e:

            print("Error:", e)

            return []


    def parse_prices(self, market):

        prices_raw = market.get("outcomePrices", "[null, null]")
        if isinstance(prices_raw, str):
            return json.loads(prices_raw)
        return prices_raw


    def get_best_market(self):

        markets = self.get_markets()

        if not markets:

            return None


        for market in markets:

            try:

                if market.get("closed"):
                    continue

                prices = self.parse_prices(market)

                if len(prices) < 2 or prices[0] is None:
                    continue

                question = market["question"]
                price = float(prices[0])

                # extraire token_id pour le trading LIVE
                token_id = None
                tokens_raw = market.get("clobTokenIds", "[]")
                if isinstance(tokens_raw, str):
                    tokens = json.loads(tokens_raw)
                else:
                    tokens = tokens_raw
                if tokens:
                    token_id = tokens[0]

                return {

                    "market": question,
                    "price": price,
                    "token_id": token_id

                }

            except:
                continue


        return None
