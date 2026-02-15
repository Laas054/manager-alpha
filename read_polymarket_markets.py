import requests
import json

API_URL = "https://gamma-api.polymarket.com/markets"

# règles Alpha simples
MIN_VOLUME = 10000       # volume minimum
MIN_PRICE = 0.05         # éviter prix trop extrêmes
MAX_PRICE = 0.95


def analyze_market(market):

    title = market.get("question", "N/A")

    prices_raw = market.get("outcomePrices", "[null, null]")
    if isinstance(prices_raw, str):
        prices = json.loads(prices_raw)
    else:
        prices = prices_raw

    yes_price = prices[0] if len(prices) > 0 else None
    no_price = prices[1] if len(prices) > 1 else None

    volume = market.get("volume", 0)

    # validation données
    if yes_price is None or no_price is None:
        return None

    yes_price = float(yes_price)
    no_price = float(no_price)
    volume = float(volume)

    # logique Alpha
    tradable = True
    reasons = []

    if volume < MIN_VOLUME:
        tradable = False
        reasons.append("volume trop faible")

    if yes_price < MIN_PRICE or yes_price > MAX_PRICE:
        tradable = False
        reasons.append("prix extrême")

    distance_from_50 = abs(yes_price - 0.50)

    if distance_from_50 < 0.05:
        tradable = False
        reasons.append("trop incertain")

    return {
        "title": title,
        "yes_price": yes_price,
        "no_price": no_price,
        "volume": volume,
        "tradable": tradable,
        "reasons": reasons
    }


def get_markets(limit=10):

    params = {"closed": "false", "limit": 100, "active": "true"}
    response = requests.get(API_URL, params=params)
    markets = response.json()

    print("\n=== ANALYSE ALPHA ===\n")

    count = 0

    for market in markets:

        if market.get("closed"):
            continue

        result = analyze_market(market)

        if result is None:
            continue

        print(f"Market: {result['title']}")
        print(f"YES: {result['yes_price']}")
        print(f"NO: {result['no_price']}")
        print(f"Volume: ${result['volume']}")

        if result["tradable"]:
            print("STATUS: TRADABLE")
        else:
            print("STATUS: REJECT")
            print("Reason:", ", ".join(result["reasons"]))

        print("-" * 50)

        count += 1

        if count >= limit:
            break


if __name__ == "__main__":
    get_markets(limit=10)
