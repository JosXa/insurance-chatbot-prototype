from abc import ABCMeta, abstractmethod

from logic.chataction import ChatAction
from model import User


class IBotAPIClient(object, metaclass=ABCMeta):
    @property
    @abstractmethod
    def client_name(self): raise NotImplementedError()

    @abstractmethod
    def initialize(self): pass

    @abstractmethod
    def start_listening(self): pass

    @abstractmethod
    def add_plaintext_handler(self, callback): pass

    @abstractmethod
    def _send_message(self, recipient: User, text: str, markup): pass

    @abstractmethod
    def add_error_handler(self, callback): pass

    @abstractmethod
    def unify_update(self, update): pass

    @abstractmethod
    def create_reply_keyboard(self, buttons, n_cols=None): pass

    @abstractmethod
    def perform_actions(self, action: ChatAction): pass
