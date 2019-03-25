from test.common_alg import AlgTestCase
from isdquantum.methods.circuits.bruteforce_circ import BruteforceISDCircuit
from isdquantum.utils import qiskit_support
from isdclassic.methods.bruteforce import Bruteforce as BruteforceClassic
from isdclassic.utils import rectangular_codes_hardcoded as rch
import numpy as np
from parameterized import parameterized
import unittest


# The idea is to first run the classical computation and
# from it obtain the V matrix. Then launch the quantum algorithm
# with this V matrix. In this way, we should run the QuantumCircuit
# just one time because it is sure that we can recover the error from this
# specific V matrix (since the classical algorithm used it to solve the
# problem)
class BruteforceCircuitTest(AlgTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import logging
        other_logger = logging.getLogger(
            'isdquantum.methods.circuits.bruteforce_circ')
        other_logger.setLevel(cls.logger.level)
        other_logger.handlers = cls.logger.handlers
        return
        other_logger = logging.getLogger('isdclassic')
        other_logger.setLevel(cls.logger.level)
        other_logger.handlers = cls.logger.handlers

    def common(self, n, k, d, w, mct_mode, nwr_mode):
        h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
            n, k, d, w)
        self.logger.info(
            "Launching TEST w/ n = {0}, k = {1}, d = {2}, w = {3}, mct_mode = {4}, nwr_mode = {5}"
            .format(n, k, d, w, mct_mode, nwr_mode))
        self.logger.debug("h = \n{0}".format(h))
        for i, s in enumerate(syndromes):
            with self.subTest(s=s):
                self.logger.info("Launching SUBTEST w/ s = {0}".format(s))
                classic_brute = BruteforceClassic(h, s, w)
                exp_e = classic_brute.run()
                # Just a double check on the result of the classic algorithm
                np.testing.assert_array_almost_equal(exp_e, errors[i])
                exp_indexes = classic_brute.result['indexes']
                self.logger.debug("exp_e_indexes {}".format(exp_indexes))

                # QUANTUM
                self.logger.info("Bruteforce Classic ended, preparing quantum")
                quantum_brute = BruteforceISDCircuit(h, s, w, False, mct_mode,
                                                     nwr_mode, None)
                qc = quantum_brute.build_circuit()
                self.logger.debug("Rounds required {}".format(
                    quantum_brute.rounds))
                result = self.execute_statevector(
                    qc, backend_options={'statevector_hpc_gate_opt': True})
                statevector_results = qiskit_support.from_statevector_to_prob_and_phase_detailed(
                    result.get_statevector(), qc)
                # print(statevector_results)
                statevector_results_selectors, _ = qiskit_support.from_prob_and_phase_detailed_to_qreg_prob(
                    statevector_results, 'select')
                # print("*****")
                # print(statevector_results_selectors)
                max_k_v = qiskit_support.get_max_from_qreg_prob(
                    statevector_results_selectors)
                self.logger.debug("max status {} with probability {}".format(
                    max_k_v[0], max_k_v[1]))
                if nwr_mode == BruteforceISDCircuit.NWR_FPC:
                    self.assertGreater(max_k_v[1], 0.9)
                error_positions = [
                    pos for pos, char in enumerate(max_k_v[0][::-1])
                    if char == '1'
                ]
                self.assertEqual(error_positions, list(exp_indexes))

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
        ("n8_k2_d5_w3", 8, 2, 5, 3),
    ])
    @unittest.skipIf(not AlgTestCase.FPC_ON, "Skipped fpc")
    def test_brute_basic_fpc(self, name, n, k, d, w):
        self.common(n, k, d, w, 'basic', 'fpc')

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
        # Statevector crash, too many qubits
        # ("n8_k2_d5_w3", 8, 2, 5, 3),
    ])
    @unittest.skipIf(not AlgTestCase.FPC_ON, "Skipped fpc")
    def test_brute_advanced_fpc(self, name, n, k, d, w):
        self.common(n, k, d, w, 'advanced', 'fpc')

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
        # 33 qubits needed, 32 available
        # ("n8_k2_d5_w3", 8, 2, 5, 3),
    ])
    @unittest.skipIf(not AlgTestCase.BENES_ON, "Skipped benes")
    def test_brute_basic_benes(self, name, n, k, d, w):
        self.common(n, k, d, w, 'basic', 'benes')

    @parameterized.expand([
        ("n4_k1_d4_w1", 4, 1, 4, 1),
        ("n7_k4_d3_w1", 7, 4, 3, 1),
        ("n8_k4_d4_w1", 8, 4, 4, 1),
        ("n8_k4_d4_w2", 8, 4, 4, 2),
        ("n8_k2_d5_w3", 8, 2, 5, 3),
    ])
    @unittest.skipIf(not AlgTestCase.BENES_ON, "Skipped benes")
    def test_brute_advanced_benes(self, name, n, k, d, w):
        self.common(n, k, d, w, 'advanced', 'benes')
