import logging
from isdquantum.utils import qiskit_support
from isdquantum.methods.circuits.bruteforce_circ import BruteforceISDCircuit
from isdquantum.methods.algorithms.abstract_alg import ISDAbstractAlg
from isdquantum.methods.algorithms.algorithm_result import AlgResult
from isdquantum.circuit import hamming_weight_generate as hwg

logger = logging.getLogger(__name__)


class BruteforceAlg(ISDAbstractAlg):
    def __init__(self, h, syndrome, w, need_measures, mct_mode, nwr_mode):
        super().__init__(h, syndrome, w, need_measures, mct_mode, nwr_mode)

    def prepare_circuit_for_backend(self, provider_name, backend_name,
                                    n_rounds):

        bru_circ = BruteforceISDCircuit(self.h, self.syndrome, self.w,
                                        self.need_measures, self.mct_mode,
                                        self.nwr_mode, n_rounds)
        qc = bru_circ.build_circuit()
        n_qubits = qc.width()
        logger.info("Number of qubits needed = {0}".format(n_qubits))
        backend = qiskit_support.get_backend(provider_name, backend_name,
                                             n_qubits)
        logger.debug("After function, backend name is {0}".format(
            backend.name()))
        return bru_circ, backend

    def run(self, provider_name, backend_name, shots=8192):
        bruci, backend = self.prepare_circuit_for_backend(
            provider_name, backend_name, None)
        qiskit_result = qiskit_support.run(bruci.circuit, backend, shots)
        counts = qiskit_result.get_counts()
        # logger.debug("counts \n{}".format(counts))
        # alg_result = self.run_circuit_on_backend(bruci.circuit, backend, shots)
        # alg_result.rounds = rounds
        # counts = alg_result.qiskit_result.get_counts()
        if self.nwr_mode == BruteforceISDCircuit.NWR_BUTTERFLY:
            per_reg_c = qiskit_support.from_global_counts_to_per_register_count(
                counts, len(bruci._butterfly_flip_q), len(bruci._selectors_q))
            logger.debug("Per register count\n{}".format(per_reg_c))
            per_reg_p = qiskit_support.from_global_counts_to_per_register_prob(
                counts, len(bruci._butterfly_flip_q), len(bruci._selectors_q))
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
                    bruci._butterfly_dict, per_reg_p[0])
                logger.debug(
                    "selectors state generated from flip is {}".format(
                        selectors_generated_state))
                selectors_final_state = selectors_generated_state
                accuracy = accuracy_flips
            else:
                selectors_final_state = selectors_state
                accuracy = selectors_accuracy
        elif self.nwr_mode == BruteforceISDCircuit.NWR_FPC:  # FPC MODE
            max_val = max(counts.values())
            accuracy = max_val / shots
            max_val_status = max(counts, key=lambda key: counts[key])
            logger.debug(
                "Max value for fpc is {0} ({2:4.2f} accuracy) for status {1}".
                format(max_val, max_val_status, accuracy))
            # qiskit state is reversed and is a string
            selectors_final_state = [int(x) for x in max_val_status[::-1]]

        logger.debug(
            "Selectors final state is {}".format(selectors_final_state))
        error = [0] * self.n
        for i, c in enumerate(selectors_final_state):
            if c == 1:
                error[i] = 1
        logger.debug("Error is {}".format(error))
        alg_result = AlgResult(bruci.circuit, error, accuracy, bruci.rounds,
                               qiskit_result)
        return alg_result
