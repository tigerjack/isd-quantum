import logging
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


class ISDAbstractAlg(ABC):
    def __init__(self, h, syndrome, w, need_measures, mct_mode, nwr_mode):
        assert w > 0, "Weight must be positive"
        assert syndrome.shape[0] == h.shape[
            0], "Syndrome should be of length r"
        self.w = w
        self.h = h
        self.syndrome = syndrome
        self.r = h.shape[0]
        self.n = h.shape[1]
        self.k = self.n - self.r
        self.need_measures = need_measures
        self.mct_mode = mct_mode
        self.nwr_mode = nwr_mode
