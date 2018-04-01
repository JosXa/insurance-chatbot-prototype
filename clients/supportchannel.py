from abc import ABCMeta, abstractmethod


class SupportChannel(object, metaclass=ABCMeta):
    """
    Base class to provide a channel where supporters get information
    """

    @abstractmethod
    def send_notification(self, message): pass

    @abstractmethod
    def send_file(self, filepath, caption=None): pass
