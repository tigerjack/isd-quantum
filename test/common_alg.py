from test.common_circuit import CircuitTestCase
from isdquantum.utils import qiskit_support
import os


class AlgTestCase(CircuitTestCase):
    BENES_ON = int(os.getenv('BENES_ON', '0'))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
