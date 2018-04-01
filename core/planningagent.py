from abc import ABCMeta, abstractmethod

from logic.sentencecomposer import SentenceComposer


class IPlanningAgent(metaclass=ABCMeta):
    """ Base class for a PlanningAgent """

    @abstractmethod
    def build_next_actions(self, context) -> SentenceComposer: pass
