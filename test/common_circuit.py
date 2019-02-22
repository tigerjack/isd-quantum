from test.common import BasicTestCase
from isdquantum.utils import misc


class CircuitTestCase(BasicTestCase):
    @staticmethod
    def draw_circuit(circuit, filename):
        misc.draw_circuit(qc, "data/img/test/" + filename)

    @staticmethod
    def execute_qasm(qc, shots=1024):
        backend = misc.get_backend('basicaer', 'qasm_simulator', qc.width())
        return misc.run(qc, backend, shots)

    @staticmethod
    def execute_statevector(qc):
        backend = misc.get_backend('basicaer', 'statevector_simulator',
                                   qc.width())
        return misc.run(qc, backend, 1)
