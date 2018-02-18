from abc import ABCMeta, abstractmethod

from logic.sentencecomposer import SentenceComposer


class IPlanningAgent(metaclass=ABCMeta):
    @abstractmethod
    def build_next_actions(self, context) -> SentenceComposer: pass


