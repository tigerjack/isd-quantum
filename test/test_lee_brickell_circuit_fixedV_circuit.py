from test.common_alg import AlgTestCase
from isdquantum.methods.circuits.lee_brickell_bruteforce_circ import LeeBrickellCircuit
from isdquantum.utils import qiskit_support
from isdquantum.circuit import hamming_weight_generate as hwg
from isdclassic.methods.lee_brickell import LeeBrickell as LeeBrickellClassic
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
class LeeBrickellCircuitTest(AlgTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import logging
        other_logger = logging.getLogger(
            'isdquantum.methods.circuits.lee_brickell_bruteforce_circ')
        other_logger.setLevel(cls.logger.level)
        other_logger.handlers = cls.logger.handlers
        return
        other_logger = logging.getLogger('isdclassic')
        other_logger.setLevel(cls.logger.level)
        other_logger.handlers = cls.logger.handlers

    def common(self, n, k, d, w, p, mct_mode, nwr_mode):
        h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
            n, k, d, w)
        self.logger.info(
            "Launching TEST w/ n = {0}, k = {1}, d = {2}, w = {3}, p = {4}, mct_mode = {5}, nwr_mode = {6}"
            .format(n, k, d, w, p, mct_mode, nwr_mode))
        self.logger.debug("h = \n{0}".format(h))
        for i, s in enumerate(syndromes):
            with self.subTest(s=s):
                self.logger.info("Launching SUBTEST w/ s = {0}".format(s))
                classic_lee = LeeBrickellClassic(h, s, w, p)
                exp_e = classic_lee.run()
                # Just a double check on the result of the classic algorithm
                np.testing.assert_array_almost_equal(exp_e, errors[i])
                hr = classic_lee.result['hr']
                perm = classic_lee.result['perm']
                s_sig = classic_lee.result['s_sig']
                u = classic_lee.result['u']
                v = classic_lee.result['v']
                exp_e_hat = classic_lee.result['e_hat']
                exp_indexes = classic_lee.result['indexes']
                self.logger.debug("v is \n{}".format(v))
                self.logger.debug("s_sig is {}".format(s_sig))

                # QUANTUM
                self.logger.info(
                    "LeeBrickell Classic ended, preparing quantum")
                wanted_sum = w - p
                shots = 4098
                quantum_lee = LeeBrickellCircuit(v, s_sig, w, p, True,
                                                 mct_mode, nwr_mode, None)
                qc = quantum_lee.build_circuit()
                self.logger.debug("Rounds required {}".format(
                    quantum_lee.rounds))
                result = self.execute_qasm(qc, shots=shots)
                counts = result.get_counts()
                # self.logger.debug(counts)
                if nwr_mode == LeeBrickellCircuit.NWR_BUTTERFLY:
                    per_reg_c = qiskit_support.from_global_counts_to_per_register_count(
                        counts, len(quantum_lee._butterfly_flip_q),
                        len(quantum_lee._selectors_q))
                    self.logger.debug(
                        "Per register count\n{}".format(per_reg_c))
                    per_reg_p = qiskit_support.from_global_counts_to_per_register_prob(
                        counts, len(quantum_lee._butterfly_flip_q),
                        len(quantum_lee._selectors_q))
                    self.logger.debug(
                        "Per register prob\n{}".format(per_reg_p))
                    flips_accuracy, flips_state = qiskit_support.from_register_prob_to_state(
                        per_reg_p[0])
                    selectors_accuracy, selectors_state = qiskit_support.from_register_prob_to_state(
                        per_reg_p[1])
                    self.logger.debug(
                        "accuracy {} for selectors state {}".format(
                            selectors_accuracy, selectors_state))
                    self.logger.debug("accuracy {} for flips state {}".format(
                        flips_accuracy, flips_state))
                    if '?' in selectors_state:
                        selectors_generated_state = hwg.generate_bits_from_flip_states(
                            quantum_lee._butterfly_dict, per_reg_p[0])
                        self.logger.debug(
                            "selectors state generated from flip is {}".format(
                                selectors_generated_state))
                        selectors_final_state = selectors_generated_state
                        accuracy = flips_accuracy
                    else:
                        selectors_final_state = selectors_state
                        accuracy = selectors_accuracy
                elif nwr_mode == LeeBrickellCircuit.NWR_FPC:  # FPC MODE
                    max_val = max(counts.values())
                    max_val_status = max(counts, key=lambda key: counts[key])
                    accuracy = max_val / shots

                    self.logger.debug(
                        "Max value for fpc is {0} ({2:4.2f} accuracy) for status {1}"
                        .format(max_val, max_val_status, accuracy))
                    # qiskit state is reversed and is a string
                    selectors_final_state = [
                        int(x) for x in max_val_status[::-1]
                    ]
                self.logger.debug("Selector finale state is {}".format(
                    selectors_final_state))

                # BUILD ERROR VECTOR
                try:
                    self.assertGreater(accuracy, 0.4)
                    error_positions = [
                        pos for pos, char in enumerate(selectors_final_state)
                        if char == 1
                    ]
                    self.assertEqual(error_positions, list(exp_indexes))
                    # self.logger.debug("Error positions {}".format(error_positions))
                    # self.logger.debug("Expected error positions {}".format(indexes))
                    v_extr = v[:, error_positions]
                    sum_to_s = (v_extr.sum(axis=1) + s_sig) % 2
                    sum_to_s_w = np.sum(sum_to_s)
                    self.assertEqual(sum_to_s_w, wanted_sum)
                    e_hat = np.concatenate((np.zeros(k), sum_to_s))
                    for j in error_positions:
                        e_hat[j] = 1
                    self.logger.debug(
                        "e_hat after error position is {}".format(e_hat))
                    np.testing.assert_array_equal(e_hat, exp_e_hat)
                    # print("expected e_hat is {}".format(exp_e_hat))
                    e_hat_w = np.sum(e_hat)
                    self.assertEqual(e_hat_w, w)
                    e = np.mod(np.dot(e_hat, perm.T), 2)
                    self.logger.info("Error {} real".format(e))
                    self.logger.info("Error {} expected".format(exp_e))
                    np.testing.assert_array_equal(e, exp_e)
                except Exception:
                    self.logger.error(
                        "Failed TEST w/ mct_mode={}, nwr_mode={}, n={}, k={}, d={}, w={}, p={} syn={}, v=\n{}"
                        .format(mct_mode, nwr_mode, n, k, d, w, p, s_sig, v))
                    self.logger.error("accuracy={}, counts\n{}".format(
                        accuracy, counts))
                    self.logger.error("Error {} expected".format(exp_e))
                    raise

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k2_d5_w3_p1", 8, 2, 5, 3, 1),
        ("n8_k2_d5_w3_p2", 8, 2, 5, 3, 2),
    ])
    @unittest.skipIf(not AlgTestCase.FPC_ON, "Skipped fpc")
    def test_fixed_v_basic_fpc(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'basic', 'fpc')

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        ("n8_k2_d5_w3_p1", 8, 2, 5, 3, 1),
        ("n8_k2_d5_w3_p2", 8, 2, 5, 3, 2),
    ])
    @unittest.skipIf(not AlgTestCase.FPC_ON, "Skipped fpc")
    def test_fixed_v_advanced_fpc(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'advanced', 'fpc')

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        # Too few flips
        # ("n8_k2_d5_w3_p1", 8, 2, 5, 3, 1),
        # No combination is possible
        # ("n8_k2_d5_w3_p2", 8, 2, 5, 3, 2),
    ])
    @unittest.skipIf(not AlgTestCase.BUTTERFLY_ON, "Skipped butterfly")
    def test_fixed_v_basic_butterfly(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'basic', 'butterfly')

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
        # Too few flips
        # ("n8_k2_d5_w3_p1", 8, 2, 5, 3, 1),
        # No combination is possible
        # ("n8_k2_d5_w3_p2", 8, 2, 5, 3, 2),
    ])
    @unittest.skipIf(not AlgTestCase.BUTTERFLY_ON, "Skipped butterfly")
    def test_fixed_v_advanced_butterfly(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'advanced', 'butterfly')
