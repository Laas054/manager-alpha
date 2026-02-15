import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class OllamaClient:

    def __init__(self):
        self.api_key = os.getenv("OLLAMA_API_KEY", "")
        self.url = "https://ollama.com/api/chat"

    def evaluate(self, market, model="deepseek-v3.2"):

        prompt = f"""Evaluate this prediction market for trading.

Market: {market['market']}
Price: {market['price']}
Volume: {market.get('volume', 'N/A')}

Rules:
- If price is far from 0.50 (strong signal), trade = true
- If price is close to 0.50 (uncertain), trade = false
- confidence must be between 0 and 1
- side = YES if you think the event will happen, NO otherwise

Return ONLY valid JSON, no other text:
{{"trade": true, "side": "YES", "confidence": 0.85}}"""

        try:
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
                timeout=60
            )

            if response.status_code != 200:
                return self._fallback(market)

            data = response.json()

            # Ollama format: message.content
            content = data.get("message", {}).get("content", "")

            if not content:
                return self._fallback(market)

            return self._parse_json(content)

        except Exception as e:
            print(f"  AI error: {e}")
            return self._fallback(market)

    def _parse_json(self, content):

        try:
            return json.loads(content.strip())
        except Exception:
            pass

        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except Exception:
                pass

        return {"trade": False, "side": "NO", "confidence": 0}

    def _fallback(self, market):

        price = market["price"]
        distance = abs(price - 0.5)

        if distance < 0.05:
            return {"trade": False, "side": "NO", "confidence": 0}

        side = "YES" if price > 0.5 else "NO"
        confidence = round(min(distance * 2, 1.0), 2)

        return {
            "trade": confidence > 0.3,
            "side": side,
            "confidence": confidence
        }
