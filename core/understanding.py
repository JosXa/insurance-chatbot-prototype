import datetime

from typing import Dict


class MessageUnderstanding:
    """
    Data holding class for an incoming utterance, enriched with NLU information.
    """

    def __init__(
            self,
            text: str,
            intent: str,
            parameters: Dict[str, str] = None,
            contexts=None,
            date: datetime.datetime = None,
            score: float = None,
            media_location: str = None):
        self.text = text
        self.intent = intent
        self.parameters = parameters if parameters else None
        self.contexts = contexts if contexts else None,
        self.score = score
        self.date = date if date else datetime.datetime.now()
        self.media_location = media_location

    def __str__(self):
        params = {k: v for k, v in self.parameters.items() if v} if self.parameters else None
        return f"Understanding('{self.intent}'" \
               f"{', ' + str(params) if params else ''})" \
               f"{', ' + str(self.contexts) if any(self.contexts) else ''}"
