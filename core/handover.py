class HumanHandover:
    """
    TODO: Not yet implemented
    """

    def __init__(self, operators=None):
        self.operators = operators if operators else []

    def register_operator(self):
        raise NotImplementedError

    def remove_operator(self, telegram_chat_id):
        raise NotImplementedError
