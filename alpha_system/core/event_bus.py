class EventBus:
    """Bus d'événements pour communication inter-composants."""

    def __init__(self):

        self.listeners = {}

        print("EventBus initialized")


    def on(self, event_name, callback):

        if event_name not in self.listeners:
            self.listeners[event_name] = []

        self.listeners[event_name].append(callback)


    def emit(self, event_name, data=None):

        if event_name not in self.listeners:
            return

        for callback in self.listeners[event_name]:
            try:
                callback(data)
            except Exception as e:
                print(f"EventBus error on '{event_name}': {e}")
