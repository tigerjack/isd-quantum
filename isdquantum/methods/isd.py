import logging
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


class ISDAbstract(ABC):
    def __init__(self, h, syndrome, w, need_measures):
        self.h = h
        self.syndrome = syndrome
        self.w = w
        self.n = h.shape[1]
        self.r = h.shape[0]
        self.need_measures = need_measures
        assert w > 0, "Weight must be positive"
        assert syndrome.shape[0] == self.r, "Syndrome should be of length r"

    @abstractmethod
    def build_circuit(self):
        pass
