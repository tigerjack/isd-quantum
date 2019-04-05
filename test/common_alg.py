from test.common_circuit import CircuitTestCase
from isdquantum.utils import qiskit_support
import os


class AlgTestCase(CircuitTestCase):
    BUTTERFLY_ON = int(os.getenv('BUTTERFLY_ON', '0'))
    FPC_ON = int(os.getenv('FPC_ON', '0'))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
