import unittest
import logging


class BasicTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(cls.__name__)
        from os import getenv
        if not getenv('LOG_LEVEL'):
            return
        logging_level = logging._nameToLevel.get(getenv('LOG_LEVEL'), 'INFO')
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(levelname)-8s %(funcName)-12s %(message)s')
        handler.setFormatter(formatter)
        cls.logger.addHandler(handler)
        cls.logger.setLevel(logging_level)

    @staticmethod
    def draw_circuit(circuit, filename):
        from qiskit.tools.visualization import circuit_drawer
        circuit_drawer(circuit, filename=filename, output='mpl')

    @staticmethod
    def execute_qasm(qc):
        from qiskit import BasicAer, execute
        backend = BasicAer.get_backend("qasm_simulator")
        job = execute(qc, backend=backend)
        counts = job.result().get_counts(qc)
        return counts
