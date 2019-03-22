import logging
from isdclassic.methods.common import ISDWithoutLists
from isdquantum.methods.circuits.lee_brickell_bruteforce_circ import LeeBrickellCircuit
from isdquantum.methods.algorithms.abstract_alg import ISDAbstractAlg
from isdquantum.utils import qiskit_support
from isdquantum.methods.algorithms.algorithm_result import AlgResult
from isdquantum.circuit import hamming_weight_generate as hwg
import numpy as np

logger = logging.getLogger(__name__)


class LeeBrickellMixedAlg(ISDAbstractAlg):
    def __init__(self, h, syndrome, w, p, need_measures, mct_mode, nwr_mode):
        super().__init__(h, syndrome, w, need_measures, mct_mode, nwr_mode)
        self.p = p

    def run(self, provider_name, backend_name, shots=8192):
        exit_condition = False
        while (not exit_condition):
            isd_classic = ISDWithoutLists(self.h, self.syndrome, self.w,
                                          ISDWithoutLists.ALG_LEE_BRICKELL)
            hr, u, perm, s_sig = isd_classic.get_matrix_rref()
            logger.debug(
                "Classical RREF end, received u\n{}\nperm\n{}\nh_rref\n{}\ns_sig {}"
                .format(u, perm, hr, s_sig))
            # Extract k-most submatrix V from hr
            v = hr[:, 0:self.k]
            logger.debug("Extracted v is\n{}".format(v))
            # Quantum algorithm to check which of the (k choose p) combination of
            # p columns, added to the syndrome, has weight w - p
            # Q.A. will return the specific combination of column
            lee_circ = LeeBrickellCircuit(v, s_sig, self.w, self.p,
                                          self.need_measures, self.mct_mode,
                                          self.nwr_mode, None)
            logger.info("Classic end, Lee bricked quantum start")
            qc = lee_circ.build_circuit()
            rounds = lee_circ.rounds
            n_qubits = qc.width()
            logger.info("Number of qubits needed = {0}".format(n_qubits))
            backend = qiskit_support.get_backend(provider_name, backend_name,
                                                 n_qubits)
            logger.debug("After function, backend name is {0}".format(
                backend.name()))
            result = qiskit_support.run(qc, backend, shots=shots)
            counts = result.get_counts(qc)

            if self.nwr_mode == LeeBrickellCircuit.NWR_BENES:
                per_reg_c = qiskit_support.from_global_counts_to_per_register_count(
                    counts, len(lee_circ._benes_flip_q),
                    len(lee_circ._selectors_q))
                logger.debug("Per register count\n{}".format(per_reg_c))
                per_reg_p = qiskit_support.from_global_counts_to_per_register_prob(
                    counts, len(lee_circ._benes_flip_q),
                    len(lee_circ._selectors_q))
                logger.debug("Per register prob\n{}".format(per_reg_p))
                flips_accuracy, flips_state = qiskit_support.from_register_prob_to_state(
                    per_reg_p[0])
                selectors_accuracy, selectors_state = qiskit_support.from_register_prob_to_state(
                    per_reg_p[1])
                logger.debug("accuracy {} for selectors state {}".format(
                    selectors_accuracy, selectors_state))
                logger.debug("accuracy {} for flips state {}".format(
                    flips_accuracy, flips_state))
                if '?' in selectors_state:
                    selectors_generated_state = hwg.generate_bits_from_flip_states(
                        lee_circ._benes_dict, per_reg_p[0])
                    logger.debug(
                        "selectors state generated from flip is {}".format(
                            selectors_generated_state))
                    selectors_final_state = selectors_generated_state
                    accuracy = flips_accuracy
                else:
                    selectors_final_state = selectors_state
                    accuracy = selectors_accuracy
            elif self.nwr_mode == LeeBrickellCircuit.NWR_FPC:  # FPC MODE
                max_val = max(counts.values())
                max_val_status = max(counts, key=lambda key: counts[key])
                accuracy = max_val / shots

                logger.debug(
                    "Max value for fpc is {0} ({2:4.2f} accuracy) for status {1}"
                    .format(max_val, max_val_status, accuracy))
                # qiskit state is reversed and is a string
                selectors_final_state = [int(x) for x in max_val_status[::-1]]

            logger.debug(
                "Selector finale state is {}".format(selectors_final_state))

            ##############
            # logger.debug("{0} counts: \n {1}".format(len(counts), counts))
            # max_val = max(counts.values())
            # accuracy = max_val / shots
            # logger.debug("Max val is {}, shots is {}, accuracy is {}".format(
            #     max_val, shots, accuracy))
            if accuracy < 0.7:
                logger.debug("Low accuracy")
                continue
            # max_val_status = max(counts, key=lambda key: counts[key])
            # logger.debug(
            #     "Max value is {} ({:4.2f} accuracy) for status {}".format(
            #         max_val, max_val / 8192, max_val_status))
            # Then e_hat = concatenate([0] * k, extract(hr, i) + s_sig
            error_positions = [
                pos for pos, char in enumerate(selectors_final_state)
                # if char == '1'
                if char == 1
            ]
            logger.debug("error positions are: {}".format(error_positions))
            v_extr = v[:, error_positions]
            sum_to_s = (v_extr.sum(axis=1) + s_sig) % 2
            logger.debug("Sum of V{} and s_sig {} is {}".format(
                error_positions, s_sig, sum_to_s))
            sum_to_s_w = np.sum(sum_to_s)
            if sum_to_s_w != self.w - self.p:
                logger.warning("Wrong sum to s {}".format(sum_to_s_w))
                continue
            e_hat = np.concatenate((np.zeros(self.k), sum_to_s))
            logger.debug("e_hat before error position is {}".format(e_hat))
            for j in error_positions:
                e_hat[j] = 1
            logger.debug("e_hat after error position is {}".format(e_hat))
            e_hat_w = np.sum(e_hat)
            logger.debug("Weight of e_hat is {}".format(e_hat_w))
            if e_hat_w == self.w:
                logger.debug("FOUND!!")
                exit_condition = True
                logger.debug("Original syndrome was {}".format(self.syndrome))
            else:
                logger.warn("Wrong e_hat_w")
        e = np.mod(np.dot(e_hat, perm.T), 2)
        alg_result = AlgResult(qc, e, accuracy, rounds, result)
        logger.info("Error is {}".format(e))
        return alg_result
