import logging
from isdclassic.methods.common import ISDWithoutLists
from isdquantum.methods.circuits.lee_brickell_bruteforce_circ import LeeBrickellCircuit
from isdquantum.methods.algorithms.abstract_alg import ISDAbstractAlg
from isdquantum.utils import misc
import numpy as np

logger = logging.getLogger(__name__)


class LeeBrickellMixedAlg(ISDAbstractAlg):
    def __init__(self, h, syndrome, w, p, need_measures, mct_mode, nwr_mode):
        super().__init__(h, syndrome, w, need_measures, mct_mode, nwr_mode)
        self.p = p

    def run(self, provider_name, backend_name):
        exit_condition = False
        while (not exit_condition):
            isd_classic = ISDWithoutLists(self.h, self.syndrome, self.w,
                                          ISDWithoutLists.ALG_LEE_BRICKELL)
            hr, u, perm, s_sig = isd_classic.get_matrix_rref()
            logger.info(
                "Classical RREF end, received u\n{}\nperm\n{}\nh_rref\n{}\ns_sig {}"
                .format(u, perm, hr, s_sig))
            # Extract k-most submatrix V from hr
            print(self.k)
            v = hr[:, 0:self.k]
            logger.info("Extracted v is\n{}".format(v))
            # TODO lee brickell should take only v as input
            # Quantum algorithm to check which of the (k choose p) combination of
            # p columns, added to the syndrome, has weight w - p
            # Q.A. will return the specific combination of column
            isd_method = LeeBrickellCircuit(hr, v, s_sig, self.w, self.p,
                                            self.need_measures, self.mct_mode,
                                            self.nwr_mode)
            logger.info("Classic end, Lee bricked quantum start")
            qc = isd_method.build_circuit()
            n_qubits = qc.width()
            logger.info("Number of qubits needed = {0}".format(n_qubits))
            backend = misc.get_backend(provider_name, backend_name, n_qubits)
            logger.debug("After function, backend name is {0}".format(
                backend.name()))
            result = misc.run(qc, backend)
            counts = result.get_counts(qc)
            logger.info("{0} counts: \n {1}".format(len(counts), counts))
            max_val = max(counts.values())
            accuracy = max_val / 8192
            if accuracy < 0.7:
                logger.info("Low accuracy")
                continue
            max_val_status = max(counts, key=lambda key: counts[key])
            logger.info(
                "Max value is {} ({:4.2f} accuracy) for status {}".format(
                    max_val, max_val / 8192, max_val_status))
            # Then e_hat = concatenate([0] * k, extract(hr, i) + s_sig
            error_positions = [
                pos for pos, char in enumerate(max_val_status[::-1])
                if char == '1'
            ]
            logger.info("error positions are: {}".format(error_positions))
            v_extr = v[:, error_positions]
            sum_to_s = (v_extr.sum(axis=1) + s_sig) % 2
            logger.info("Sum of V{} and s_sig {} is {}".format(
                error_positions, s_sig, sum_to_s))
            sum_to_s_w = np.sum(sum_to_s)
            if sum_to_s_w != self.w - self.p:
                logger.warn("Wrong sum to s {}".format(sum_to_s_w))
                continue
            e_hat = np.concatenate((np.zeros(self.k), sum_to_s))
            logger.info("e_hat before error position is {}".format(e_hat))
            for j in error_positions:
                e_hat[j] = 1
            logger.info("e_hat after error position is {}".format(e_hat))
            e_hat_w = np.sum(e_hat)
            print("Weight of e_hat is {}".format(e_hat_w))
            if e_hat_w == self.w:
                print("FOUND!!")
                exit_condition = True
            logger.info("Original syndrome was {}".format(self.syndrome))
        e = np.mod(np.dot(e_hat, perm.T), 2)
        logger.info("Error is {}".format(e))
        return qc, result, e, accuracy
