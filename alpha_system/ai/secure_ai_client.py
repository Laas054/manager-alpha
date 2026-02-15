import json
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class SecureAIClient:
    """Client IA sécurisé — validation, retry, fallback, benchmark."""

    def __init__(self, config):

        self.api_key = os.getenv("OLLAMA_API_KEY", "")
        self.url = "https://ollama.com/api/chat"
        self.timeout = 60
        self.max_retries = 2
        self.confidence_threshold = config["CONFIDENCE_THRESHOLD"]

        # Benchmark
        self.total_calls = 0
        self.successful_calls = 0
        self.fallback_calls = 0
        self.total_latency = 0

    def evaluate(self, market, model="deepseek-v3.2"):
        """Évalue un marché avec validation complète de la réponse."""

        self.total_calls += 1

        prompt = f"""Evaluate this prediction market for trading.

Market: {market['market']}
Price: {market['price']}
Volume: {market.get('volume', 'N/A')}

Rules:
- If price is far from 0.50 (strong signal), trade = true
- If price is close to 0.50 (uncertain), trade = false
- confidence must be between 0 and 1
- side = YES if you think the event will happen, NO otherwise

Return ONLY valid JSON:
{{"trade": true, "side": "YES", "confidence": 0.85}}"""

        # Retry loop
        for attempt in range(self.max_retries + 1):
            try:
                start = time.time()

                response = requests.post(
                    self.url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    },
                    timeout=self.timeout
                )

                latency = time.time() - start
                self.total_latency += latency

                if response.status_code != 200:
                    if attempt < self.max_retries:
                        time.sleep(2)
                        continue
                    return self._fallback(market, model)

                data = response.json()
                content = data.get("message", {}).get("content", "")

                if not content:
                    if attempt < self.max_retries:
                        continue
                    return self._fallback(market, model)

                result = self._parse_and_validate(content)

                if result is None:
                    if attempt < self.max_retries:
                        continue
                    return self._fallback(market, model)

                self.successful_calls += 1
                result["model"] = model
                result["latency"] = round(latency, 2)
                result["source"] = "ai"
                return result

            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(2)
                    continue
                return self._fallback(market, model)

        return self._fallback(market, model)

    def _parse_and_validate(self, content):
        """Parse et valide strictement la réponse IA."""

        parsed = None

        try:
            parsed = json.loads(content.strip())
        except Exception:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(content[start:end])
                except Exception:
                    return None

        if parsed is None:
            return None

        # Validation stricte
        if "trade" not in parsed:
            return None

        if "side" not in parsed or parsed["side"] not in ("YES", "NO"):
            return None

        if "confidence" not in parsed:
            return None

        confidence = parsed["confidence"]
        if not isinstance(confidence, (int, float)):
            return None
        if confidence < 0 or confidence > 1:
            return None

        return {
            "trade": bool(parsed["trade"]),
            "side": parsed["side"],
            "confidence": round(float(confidence), 4),
        }

    def _fallback(self, market, model="unknown"):
        """Décision locale si l'IA est indisponible."""

        self.fallback_calls += 1

        price = market["price"]
        distance = abs(price - 0.5)

        if distance < 0.10:
            return {
                "trade": False, "side": "NO", "confidence": 0,
                "model": model, "source": "fallback"
            }

        side = "YES" if price > 0.5 else "NO"
        confidence = round(min(distance * 2, 0.95), 2)

        return {
            "trade": confidence > 0.3,
            "side": side,
            "confidence": confidence,
            "model": model,
            "source": "fallback"
        }

    def get_benchmark(self):

        avg_latency = round(self.total_latency / max(1, self.total_calls), 2)
        success_rate = round(self.successful_calls / max(1, self.total_calls) * 100, 1)

        return {
            "total_calls": self.total_calls,
            "successful": self.successful_calls,
            "fallbacks": self.fallback_calls,
            "success_rate": success_rate,
            "avg_latency": avg_latency,
        }
