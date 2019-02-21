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
    def execute_qasm(qc, shots=1024):
        from qiskit import BasicAer, execute
        backend = BasicAer.get_backend("qasm_simulator")
        job = execute(qc, backend=backend, shots=shots)
        result = job.result()
        # counts = job.result().get_counts(qc)
        return result

    @staticmethod
    def execute_statevector(qc):
        from qiskit import BasicAer, execute
        backend = BasicAer.get_backend("statevector_simulator")
        job = execute(qc, backend=backend)
        result = job.result()
        return result
