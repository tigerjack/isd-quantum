import logging
from parameterized import parameterized
from test.common_circuit import CircuitTestCase
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
        # other_logger = logging.getLogger('isdquantum.methods.algorithms')
        # other_logger.setLevel(cls.logger.level)
        # other_logger.handlers = cls.logger.handlers
        # other_logger = logging.getLogger('isdquantum.methods.circuits')
        # other_logger.setLevel(cls.logger.level)
        # other_logger.handlers = cls.logger.handlers

    def common(self, name, n, k, d, w, p, mct_mode, nwr_mode):
        h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
            n, k, d, w)
        self.logger.info(
            "Launching TEST {} w/ n={}, k={}, d={}, w={}, p={}, mct_mode={}, nwr_mode={}"
            .format(name, n, k, d, w, p, mct_mode, nwr_mode))
        self.logger.debug("h = \n{0}".format(h))
        for i, s in enumerate(syndromes):
            with self.subTest(s=s):
                try:
                    self.logger.info("Starting SUBTEST w/ s {}".format(s))
                    lee = LeeBrickellMixedAlg(h, s, w, p, True, 'advanced',
                                              'benes')
                    alg_result = lee.run('aer', 'qasm_simulator')
                    self.logger.debug("Rounds required {}".format(
                        alg_result.rounds))
                    counts = alg_result.qiskit_result.get_counts()
                    self.logger.debug(counts)
                    self.assertGreater(alg_result.accuracy, 2 / 3)
                    np.testing.assert_array_equal(alg_result.error, errors[i])
                except Exception:
                    self.logger.error(
                        "Failed TEST w/ n={}, k={}, d={}, w={}, p={}, syn={}, h=\n{}"
                        .format(n, k, d, w, p, s, h))
                    self.logger.error("accuracy={}, counts\n{}".format(
                        alg_result.accuracy, counts))
                    raise

    @parameterized.expand([
        ("n7_k4_d3_w1_p1", 7, 4, 3, 1, 1),
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k4_d4_w2_p2", 8, 4, 4, 2, 2),
    ])
    def test_lee_alg_basic_benes(self, name, n, k, d, w, p):
        self.common(name, n, k, d, w, p, 'basic', 'benes')

    @parameterized.expand([
        ("n7_k4_d3_w1_p1", 7, 4, 3, 1, 1),
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k4_d4_w2_p2", 8, 4, 4, 2, 2),
    ])
    def test_lee_alg_basic_fpc(self, name, n, k, d, w, p):
        self.common(name, n, k, d, w, p, 'basic', 'fpc')

    @parameterized.expand([
        ("n7_k4_d3_w1_p1", 7, 4, 3, 1, 1),
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k4_d4_w2_p2", 8, 4, 4, 2, 2),
    ])
    def test_lee_alg_advanced_benes(self, name, n, k, d, w, p):
        self.common(name, n, k, d, w, p, 'advanced', 'benes')

    @parameterized.expand([
        ("n7_k4_d3_w1_p1", 7, 4, 3, 1, 1),
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k4_d4_w2_p2", 8, 4, 4, 2, 2),
    ])
    def test_lee_alg_advanced_fpc(self, name, n, k, d, w, p):
        self.common(name, n, k, d, w, p, 'advanced', 'fpc')
