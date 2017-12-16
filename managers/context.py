from model.update import Update


class ContextManager:
    def __init__(self):
        self._updates = list()

    def add_update(self, update: Update): self._updates.append(update)




