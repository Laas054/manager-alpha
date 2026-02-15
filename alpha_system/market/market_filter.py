import json


class MarketFilter:
    """Filtre les marchés selon les critères Alpha."""

    def __init__(self, min_volume=10000, min_edge=0.05):

        self.min_volume = min_volume
        self.min_edge = min_edge

        print(f"MarketFilter initialized (min_vol:{min_volume} min_edge:{min_edge})")


    def parse_prices(self, market):

        prices_raw = market.get("outcomePrices", "[null, null]")
        if isinstance(prices_raw, str):
            return json.loads(prices_raw)
        return prices_raw


    def parse_token_ids(self, market):

        tokens_raw = market.get("clobTokenIds", "[]")
        if isinstance(tokens_raw, str):
            return json.loads(tokens_raw)
        return tokens_raw


    def filter(self, markets):
        """Retourne uniquement les marchés tradables."""

        tradable = []

        for market in markets:

            try:

                if market.get("closed"):
                    continue

                prices = self.parse_prices(market)
                if len(prices) < 2 or prices[0] is None:
                    continue

                price = float(prices[0])
                volume = float(market.get("volume", 0))

                if volume < self.min_volume:
                    continue

                if abs(price - 0.5) < self.min_edge:
                    continue

                tokens = self.parse_token_ids(market)

                tradable.append({
                    "market": market["question"],
                    "price": price,
                    "volume": volume,
                    "token_id": tokens[0] if tokens else None,
                    "raw": market
                })

            except:
                continue

        return tradable
