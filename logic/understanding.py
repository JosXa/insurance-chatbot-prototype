import datetime


class MessageUnderstanding:
    def __init__(self, text, intent, parameters=None, contexts=None, date=None, score=None):
        self.text = text
        self.intent = intent
        self.parameters = parameters if parameters else None
        self.contexts = contexts if contexts else None,
        self.score = score
        self.date = date if date else datetime.datetime.now()

    def __str__(self):
        return f"{self.intent} -- {self.parameters} -- {self.contexts}"
