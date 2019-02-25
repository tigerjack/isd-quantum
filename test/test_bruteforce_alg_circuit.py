from test.common_circuit import CircuitTestCase
from isdquantum.methods.algorithms.bruteforce_alg import BruteforceAlg
from isdclassic.utils import rectangular_codes_hardcoded as rch
import numpy as np
from parameterized import parameterized
import unittest


# The idea is to directly use the lee brickell mixed algorithm
# The test may be very slow since the classical computation can return us
# a RREF matrix which is not the one which can we use to solve the ISD problem.
# So, the RREF matrix computation should be redone several times, and so is the
# circuit building and launching
class BruteforceAlgTest(CircuitTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pass
        import logging
        other_logger = logging.getLogger('isdquantum.methods.algorithms')
        other_logger.setLevel(cls.logger.level)
        other_logger.handlers = cls.logger.handlers
        other_logger = logging.getLogger('isdquantum.methods.circuits')
        other_logger.setLevel(cls.logger.level)
        other_logger.handlers = cls.logger.handlers

    def common(self, name, n, k, d, w, mct_mode, nwr_mode):
        h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
            n, k, d, w)
        self.logger.info(
            "Launching TEST {} w/ n={}, k={}, d={}, w={}, mct_mode={}, nwr_mode={}"
            .format(name, n, k, d, w, mct_mode, nwr_mode))
        self.logger.debug("h = \n{0}".format(h))
        for i, s in enumerate(syndromes):
            with self.subTest(s=s):
                try:
                    self.logger.info("Starting SUBTEST w/ s {}".format(s))
                    bru = BruteforceAlg(h, s, w, True, mct_mode, nwr_mode)
                    alg_result = bru.run('aer', 'qasm_simulator')
                    self.logger.debug("Rounds required {}".format(
                        alg_result.rounds))
                    counts = alg_result.qiskit_result.get_counts()
                    self.logger.debug(counts)
                    self.logger.debug("accuracy={}".format(
                        alg_result.accuracy))
                    self.assertGreater(alg_result.accuracy, 2 / 3)
                    np.testing.assert_array_equal(alg_result.error, errors[i])
                except Exception:
                    self.logger.error(
                        "Failed TEST w/ n={}, k={}, d={}, w={}, syn={}, h=\n{}"
                        .format(n, k, d, w, s, h))
                    self.logger.error("accuracy={}, counts\n{}".format(
                        alg_result.accuracy, counts))
                    raise

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
    ])
    def test_brute_basic_benes(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'basic', 'benes')

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
    ])
    def test_brute_basic_fpc(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'basic', 'fpc')

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
    ])
    def test_brute_advanced_benes(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'advanced', 'benes')

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
    ])
    def test_brute_advanced_fpc(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'advanced', 'fpc')

    @parameterized.expand([
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
    ])
    @unittest.skipIf(not CircuitTestCase.SLOW_TEST, "Skipped slow test")
    def test_brute_basic_benes_slow(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'basic', 'benes')

    @parameterized.expand([
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
    ])
    @unittest.skipIf(not CircuitTestCase.SLOW_TEST, "Skipped slow test")
    def test_brute_basic_fpc_slow(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'basic', 'fpc')

    @parameterized.expand([
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
    ])
    @unittest.skipIf(not CircuitTestCase.SLOW_TEST, "Skipped slow test")
    def test_brute_advanced_benes_slow(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'advanced', 'benes')

    @parameterized.expand([
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
    ])
    @unittest.skipIf(not CircuitTestCase.SLOW_TEST, "Skipped slow test")
    def test_brute_advanced_fpc_slow(self, name, n, k, d, w):
        self.common(name, n, k, d, w, 'advanced', 'fpc')
