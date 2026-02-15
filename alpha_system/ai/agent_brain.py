from alpha_system.ai.ollama_client import OllamaClient


class AgentBrain:

    def __init__(self, model="deepseek-v3.2"):
        self.model = model
        self.client = OllamaClient()

    def evaluate(self, market):
        return self.client.evaluate(market, model=self.model)
