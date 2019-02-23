import logging
from parameterized import parameterized
from test.common_circuit import CircuitTestCase
from test.common_circuit import BasicTestCase
from isdquantum.methods.circuits.lee_brickell_bruteforce_circ import LeeBrickellCircuit
from isdclassic.methods.lee_brickell import LeeBrickell
from isdclassic.utils import rectangular_codes_hardcoded as rch
import numpy as np


# The idea is to first run the classical computation and
# from it obtain the V matrix. Then launch the quantum algorithm
# with this V matrix. In this way, we should run the QuantumCircuit
# just one time because it is sure that we can recover the error from this
# specific V matrix (since the classical algorithm used it to solve the
# problem)
class LeeBrickellCircuitTest(CircuitTestCase):
    @classmethod
    def setUpClass(cls):
        CircuitTestCase.setUpClass()
        # other_logger = logging.getLogger('isdclassic')
        # other_logger.setLevel(cls.logger.level)
        # other_logger.handlers = cls.logger.handlers
        other_logger = logging.getLogger(
            'isdquantum.methods.circuits.lee_brickell_bruteforce_circ')
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
                lee = LeeBrickell(h, s, w, p)
                exp_e = lee.run()
                self.logger.debug(
                    "For s = {0}, w = {1}, p = {2} h = \n{3}\nerror is {4}".
                    format(s, w, p, h, exp_e))
                # Just a double check on the result of the classic algorithm
                np.testing.assert_array_almost_equal(exp_e, errors[i])
                self.logger.info(
                    "LeeBrickell Classic ended, preparing quantum")
                # for k, v in lee.result.items():
                #     print("{} -> {}".format(k, v))
                hr = lee.result['hr']
                perm = lee.result['perm']
                s_sig = lee.result['s_sig']
                u = lee.result['u']
                v = lee.result['v']
                exp_e_hat = lee.result['e_hat']
                exp_indexes = lee.result['indexes']
                # print(v)
                # print(s_sig)

                # QUANTUM
                wanted_sum = w - p
                shots = 4098
                # print("v =\n{}".format(v))
                # print("s_sig = ".format(s_sig))
                lb = LeeBrickellCircuit(v, s_sig, w, p, True, mct_mode,
                                        nwr_mode)
                qc = lb.build_circuit()
                result = self.execute_qasm(qc, shots=shots)
                counts = result.get_counts()
                self.logger.info(counts)

                # BUILD ERROR VECTOR
                max_val = max(counts.values())
                max_val_status = max(counts, key=lambda key: counts[key])
                accuracy = max_val / shots
                self.assertGreater(accuracy, 2 / 3)
                error_positions = [
                    pos for pos, char in enumerate(max_val_status[::-1])
                    if char == '1'
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
                np.testing.assert_array_equal(e, exp_e)

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
    ])
    def test_fixed_v_basic_benes(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'basic', 'benes')

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
    ])
    def test_fixed_v_advanced_benes(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'advanced', 'benes')

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
    ])
    def test_fixed_v_basic_fpc(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'basic', 'fpc')

    @parameterized.expand([
        ("n8_k4_d4_w2_p1", 8, 4, 4, 2, 1),
    ])
    def test_fixed_v_advanced_fpc(self, name, n, k, d, w, p):
        self.common(n, k, d, w, p, 'advanced', 'fpc')
