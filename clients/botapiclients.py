from abc import ABCMeta, abstractmethod


class IBotAPIClient(object, metaclass=ABCMeta):
    @abstractmethod
    def initialize(self): pass

    @abstractmethod
    def start_listening(self): pass

    @abstractmethod
    def send_message(self): pass

    @abstractmethod
    def send_message(self): pass
