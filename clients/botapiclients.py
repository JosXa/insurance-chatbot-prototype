from abc import ABCMeta, abstractmethod


class IBotAPIClient(object, metaclass=ABCMeta):
    @abstractmethod
    def initialize(self): pass

    @abstractmethod
    def start_listening(self): pass

    @abstractmethod
    def add_plaintext_handler(self, callback): pass

    @abstractmethod
    def send_message(self, recipient, text): pass

    @abstractmethod
    def add_error_handler(self, callback): pass
