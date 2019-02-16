from test.common import BasicTestCase


class CircuitTestCase(BasicTestCase):
    @staticmethod
    def draw_circuit(circuit, filename):
        from qiskit.tools.visualization import circuit_drawer
        circuit_drawer(
            circuit,
            filename="data/img/test/" + filename + '.png',
            output='mpl')

    @staticmethod
    def execute_qasm(qc):
        from qiskit import BasicAer, execute
        backend = BasicAer.get_backend("qasm_simulator")
        job = execute(qc, backend=backend)
        counts = job.result().get_counts(qc)
        return counts

    @staticmethod
    def execute_statevector(qc):
        from qiskit import BasicAer, execute
        backend = BasicAer.get_backend("statevector_simulator")
        job = execute(qc, backend=backend)
        counts = job.result().get_statevector(qc)
        return counts
