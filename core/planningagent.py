from abc import ABCMeta, abstractmethod

from logic.responsecomposer import ResponseComposer


class IPlanningAgent(metaclass=ABCMeta):
    """ Base class for a PlanningAgent """

    @abstractmethod
    def build_next_actions(self, context) -> ResponseComposer: pass
