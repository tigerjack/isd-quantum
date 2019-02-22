import logging
from parameterized import parameterized
from test.common_circuit import CircuitTestCase
from test.common_circuit import BasicTestCase
from isdquantum.methods.algorithms.lee_brickell_mixed_alg import LeeBrickellMixedAlg
from isdclassic.methods.lee_brickell import LeeBrickell
from isdclassic.utils import rectangular_codes_hardcoded as rch
import numpy as np
import sys


# The idea is to directly use the lee brickell mixed algorithm
# The test may be very slow since the classical computation can return us
# a RREF matrix which is not the one which can we use to solve the ISD problem.
# So, the RREF matrix computation should be redone several times, and so is the
# circuit building and launching
class LeeBrickellAlgTest(CircuitTestCase):
    @classmethod
    def setUpClass(cls):
        CircuitTestCase.setUpClass()
        # other_logger = logging.getLogger('isdclassic')
        # other_logger.setLevel(cls.logger.level)
        # other_logger.handlers = cls.logger.handlers
        other_logger = logging.getLogger(
            'isdquantum.methods.algorithms.lee_brickell_mixed_alg')
        other_logger.setLevel(cls.logger.level)
        other_logger.handlers = cls.logger.handlers

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k4_d4_w2_p2", 8, 4, 4, 2, 2),
    ])
    def test_algorithm_benes(self, name, n, k, d, w, p):
        h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
            n, k, d, w)
        self.logger.info(
            "Launching TEST w/ n = {0}, k = {1}, d = {2}, w = {3}, p = {4}".
            format(n, k, d, w, p))
        self.logger.debug("h = \n{0}".format(h))
        for i, s in enumerate(syndromes):
            with self.subTest(s=s):
                self.logger.info("Starting subtest w/ s {}".format(s))
                lee = LeeBrickellMixedAlg(h, s, w, p, True, 'advanced',
                                          'benes')
                qc, result, e, accuracy = lee.run('aer', 'qasm_simulator')
                counts = result.get_counts()
                self.logger.debug(counts)
                self.assertGreater(accuracy, 2 / 3)
                np.testing.assert_array_equal(e, errors[i])

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k4_d4_w2_p2", 8, 4, 4, 2, 2),
    ])
    def test_algorithm_fpc(self, name, n, k, d, w, p):
        h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
            n, k, d, w)
        self.logger.info(
            "Launching TEST w/ n = {0}, k = {1}, d = {2}, w = {3}, p = {4}".
            format(n, k, d, w, p))
        self.logger.debug("h = \n{0}".format(h))
        for i, s in enumerate(syndromes):
            with self.subTest(s=s):
                self.logger.info("Starting subtest w/ s {}".format(s))
                lee = LeeBrickellMixedAlg(h, s, w, p, True, 'advanced', 'fpc')
                qc, result, e, accuracy = lee.run('aer', 'qasm_simulator')
                counts = result.get_counts()
                self.logger.debug(counts)
                self.assertGreater(accuracy, 2 / 3)
                np.testing.assert_array_equal(e, errors[i])
