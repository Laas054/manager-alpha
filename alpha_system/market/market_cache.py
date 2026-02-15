from datetime import datetime, UTC


class MarketCache:

    def __init__(self, ttl_seconds=60):

        self.cache = {}
        self.ttl = ttl_seconds

        print("MarketCache initialized (TTL:", ttl_seconds, "s)")


    def get(self, key):

        if key not in self.cache:
            return None

        entry = self.cache[key]
        age = (datetime.now(UTC) - entry["timestamp"]).total_seconds()

        if age > self.ttl:
            del self.cache[key]
            return None

        return entry["data"]


    def set(self, key, data):

        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now(UTC)
        }


    def clear(self):

        self.cache.clear()
