class AgentSelector:

    def __init__(self):

        self.agents = []

        print("AgentSelector initialized")


    def register(self, name, performance):

        self.agents.append({
            "name": name,
            "performance": performance
        })


    def select_best(self):

        if not self.agents:
            return None

        return sorted(
            self.agents,
            key=lambda x: x["performance"],
            reverse=True
        )[0]


    def report(self):

        print("\n=== AGENT RANKING ===")

        for i, agent in enumerate(sorted(
            self.agents,
            key=lambda x: x["performance"],
            reverse=True
        )):
            print(f"  {i+1}. {agent['name']} — perf: {agent['performance']}")
