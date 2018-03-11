from abc import ABCMeta, abstractmethod
from typing import TypeVar

ChatAction = TypeVar('ChatAction')


class IBotAPIClient(object, metaclass=ABCMeta):
    @property
    @abstractmethod
    def client_name(self): pass

    @abstractmethod
    def initialize(self): pass

    @abstractmethod
    def start_listening(self): pass

    @abstractmethod
    def add_plaintext_handler(self, callback): pass

    @abstractmethod
    def download_voice(self, voice_id, filepath): pass

    @abstractmethod
    def add_voice_handler(self, callback): pass

    @abstractmethod
    def add_media_handler(self, callback): pass

    @abstractmethod
    def set_start_handler(self, callback): pass

    @abstractmethod
    def add_error_handler(self, callback): pass

    @abstractmethod
    def unify_update(self, update): pass

    @abstractmethod
    def perform_action(self, action: ChatAction): pass

    @abstractmethod
    def show_typing(self, user): pass
