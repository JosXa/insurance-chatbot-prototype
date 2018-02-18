class HumanHandover:
    def __init__(self, operators=None):
        self.operators = operators if operators else []

    def register_operator(self, telegram_chat_id):
        self.operators.append(telegram_chat_id)

    def remove_operator(self, telegram_chat_id):
        self.operators.remove(telegram_chat_id)
