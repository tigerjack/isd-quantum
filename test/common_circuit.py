from test.common import BasicTestCase
from isdquantum.utils import qiskit_support


class CircuitTestCase(BasicTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @staticmethod
    def draw_circuit(circuit, filename):
        qiskit_support.draw_circuit(circuit, "data/img/test/" + filename)

    @staticmethod
    def execute_qasm(qc, shots=1024):
        backend = qiskit_support.get_backend('basicaer', 'qasm_simulator',
                                             qc.width())
        return qiskit_support.run(qc, backend, shots)

    @staticmethod
    def execute_statevector(qc):
        backend = qiskit_support.get_backend(
            'basicaer', 'statevector_simulator', qc.width())
        return qiskit_support.run(qc, backend, 1)
