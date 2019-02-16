import logging
from isdquantum.methods.isd import ISDAbstract

_logger = logging.getLogger(__name__)


class LeeBrickellISD(ISDAbstract):
    def __init__(self, h, syndrome, w, need_measures, mct_mode):
        super().__init__(h, syndrome, w, need_measures)

    def build_circuit():
        print("Hello")
