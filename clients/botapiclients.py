from abc import ABCMeta, abstractmethod
from typing import TypeVar, List

ChatAction = TypeVar('ChatAction')


class BotAPIClient(object, metaclass=ABCMeta):
    """
    Base class for a Chatbot client.
    In order to add another bot platform to the system, inherit from this class and implement all methods accordingly.
    """

    @property
    @abstractmethod
    def client_name(self) -> str: pass

    @abstractmethod
    def initialize(self):
        """ Called to set internal state and perform additional initialization """
        pass

    @abstractmethod
    def start_listening(self):
        """ Start receiving updates by webhook or long polling """
        pass

    @abstractmethod
    def add_plaintext_handler(self, callback):
        """ Adds a handler filtering only plain text updates """
        pass

    @abstractmethod
    def download_voice(self, voice_id, filepath):
        """ Downloads a voice message from the bot API """
        pass

    @abstractmethod
    def add_voice_handler(self, callback):
        """ Adds a handler filtering only voice memo updates """
        pass

    @abstractmethod
    def add_media_handler(self, callback):
        """ Adds a handler filtering media (photo, video, sticker, gif, etc.) updates """
        pass

    @abstractmethod
    def set_start_handler(self, callback):
        """ Adds the start handler, called when the bot is started by the user """
        pass

    @abstractmethod
    def add_error_handler(self, callback):
        """
        Adds an error handler, called when the internal update processing fails
        with exception
        """
        pass

    @abstractmethod
    def unify_update(self, update):
        """
        Creates the internal `Update` object our backend works with
        from whatever type of update or event this particular bot API uses.
        """
        pass

    @abstractmethod
    def perform_actions(self, actions: List[ChatAction]):
        """
        Performs a sequence of `ChatActions` planned by the `DialogManager`
        """
        pass

    @abstractmethod
    def show_typing(self, user):
        """
        Displays an "is typing" notification to the user
        """
        pass
