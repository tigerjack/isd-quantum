import logging
from math import factorial
from parameterized import parameterized
from test.common_circuit import CircuitTestCase
from isdquantum.circuit import hamming_weight_generate as hwg
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit


class BenesTestCase(CircuitTestCase):
    @classmethod
    def setUpClass(cls):
        CircuitTestCase.setUpClass()
        perm_logger = logging.getLogger('isdquantum.circuit.hamming_weight')
        perm_logger.setLevel(cls.logger.level)
        perm_logger.handlers = cls.logger.handlers

    def setUp(self):
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
    def test_patterns(self, name, n, w, reverse):
        permutation_dict = hwg.generate_qubits_with_given_weight_butterfly_get_pattern(
            n, w)
        self.logger.debug("n_flips = {0}".format(permutation_dict['n_flips']))
        self.logger.debug("n_lines = {0}".format(permutation_dict['n_lines']))
        selectors_q = QuantumRegister(permutation_dict['n_lines'], 'sel')
        flip_q = QuantumRegister(permutation_dict['n_flips'], 'flips')
        self.circuit.add_register(selectors_q)
        self.circuit.add_register(flip_q)
        self.logger.debug(flip_q.size)

        self.circuit.h(flip_q)
        for i in range(permutation_dict['to_negate_range']):
            self.circuit.x(selectors_q[i])
        for i in permutation_dict['swaps_pattern']:
            self.circuit.cswap(flip_q[i[0]], selectors_q[i[1]],
                               selectors_q[i[2]])
        if reverse:
            for i in permutation_dict['swaps_pattern'][::-1]:
                self.circuit.cswap(flip_q[i[0]], selectors_q[i[1]],
                                   selectors_q[i[2]])
        if (permutation_dict['negated_permutation']):
            self.circuit.x(selectors_q)

        # QASM SIMULATOR
        cr = ClassicalRegister(n)
        self.circuit.add_register(cr)
        self.circuit.measure(selectors_q, cr)

        counts = CircuitTestCase.execute_qasm(self.circuit).get_counts()
        counts_exp = 1 if reverse else factorial(n) / factorial(w) / factorial(
            n - w)
        self.assertEqual(len(counts), counts_exp)
