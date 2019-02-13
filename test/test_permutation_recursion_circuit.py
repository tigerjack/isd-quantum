import unittest
import logging
from math import factorial
from parameterized import parameterized
import mock
import numpy as np
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import BasicAer, execute
from isdquantum.utils import permutation_recursion


def draw_circuit(circuit, n, w):
    from qiskit.tools.visualization import circuit_drawer
    circuit_drawer(
        circuit, filename='test_rec_{0}_{1}'.format(n, w), output='mpl')


class PermRecTestCase(unittest.TestCase):
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

        perm_logger = logging.getLogger('experiments.permutation_recursion')
        perm_logger.addHandler(handler)
        perm_logger.setLevel(logging_level)

    def setUp(self):
        self.prange_isd_mock = mock.Mock()
        self.circuit = QuantumCircuit()

    @parameterized.expand([
        ('n4w1', 4, 1, False),
        ('n4w1r', 4, 1, True),
        ('n4w2', 4, 2, False),
        ('n4w2r', 4, 2, True),
        ('n4w3', 4, 3, False),
        ('n4w3r', 4, 3, True),
        ('n8w1', 8, 1, False),
        ('n8w1r', 8, 1, True),
        ('n8w2', 8, 2, False),
        ('n8w2r', 8, 2, True),
        ('n8w3', 8, 3, False),
        ('n8w3r', 8, 3, True),
        ('n8w4', 8, 4, False),
        ('n8w4r', 8, 4, True),
        ('n8w5', 8, 5, False),
        ('n8w5r', 8, 5, True),
        ('n8w6', 8, 6, False),
        ('n8w6r', 8, 6, True),
        ('n8w7', 8, 7, False),
        ('n8w7r', 8, 7, True),
        # ('n16w1', 16, 1, False),
        # ('n16w1r', 16, 1, True),
    ])
    # @unittest.skip("No reason")
    def test_patterns(self, name, n, w, reverse):
        try:
            self.prange_isd_mock.n = n
            self.prange_isd_mock.w = w
            permutation_recursion.permutation_pattern(self.prange_isd_mock)
            ##
            self.logger.debug(self.prange_isd_mock.permutation['n_flips'])
            self.logger.debug(self.prange_isd_mock.permutation['n_selectors'])
            selectors_q = QuantumRegister(
                self.prange_isd_mock.permutation['n_selectors'], 'sel')
            flip_q = QuantumRegister(
                self.prange_isd_mock.permutation['n_flips'], 'n_flips')
            self.circuit.add_register(selectors_q)
            self.circuit.add_register(flip_q)
            self.logger.debug(flip_q.size)

            self.circuit.h(flip_q)
            if (w > selectors_q.size / 2):
                to_negate_range = selectors_q.size - w
            else:
                to_negate_range = w
            for i in range(to_negate_range):
                self.circuit.x(selectors_q[i])

            for i in self.prange_isd_mock.permutation['swaps_qubits_pattern']:
                self.circuit.cswap(flip_q[i[0]], selectors_q[i[1]],
                                   selectors_q[i[2]])
            if reverse:
                for i in self.prange_isd_mock.permutation[
                        'swaps_qubits_pattern'][::-1]:
                    self.circuit.cswap(flip_q[i[0]], selectors_q[i[1]],
                                       selectors_q[i[2]])
            if (w > selectors_q.size / 2):
                self.circuit.x(selectors_q)

            # QASM SIMULATOR
            cr = ClassicalRegister(n)
            self.circuit.add_register(cr)
            self.circuit.measure(selectors_q, cr)

            counts = execute(
                self.circuit,
                BasicAer.get_backend('qasm_simulator'),
                shots=1024).result().get_counts()
            counts_exp = 1 if reverse else factorial(n) / factorial(
                w) / factorial(n - w)
            self.assertEqual(len(counts), counts_exp)
        except:
            self.logger.error("Drawing circuit")
            draw_circuit(self.circuit, n, w)
            raise
