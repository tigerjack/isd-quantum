import logging
from isdquantum.utils import qiskit_support
from isdquantum.methods.circuits.bruteforce_circ import BruteforceISDCircuit
from isdquantum.methods.algorithms.abstract_alg import ISDAbstractAlg
from isdquantum.methods.algorithms.algorithm_result import AlgResult

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
        return qc, backend, bru_circ.rounds

    def run_circuit_on_backend(self, qc, backend, shots=1024):
        result = qiskit_support.run(qc, backend, shots)
        counts = result.get_counts(qc)
        max_val = max(counts.values())
        accuracy = max_val / shots
        max_val_status = max(counts, key=lambda key: counts[key])
        logger.info(
            "Max value is {0} ({2:4.2f} accuracy) for status {1}".format(
                max_val, max_val_status, accuracy))

        error = [0] * self.n
        for i, c in enumerate(max_val_status[::-1]):
            if c == '1':
                error[i] = 1
        alg_result = AlgResult(qc, error, accuracy, None, result)
        return alg_result

    def run(self, provider_name, backend_name, shots=8192):

        if self.nwr_mode == BruteforceISDCircuit.NWR_BENES:
            n_rounds = 1
        else:
            n_rounds = None

        qc, backend, rounds = self.prepare_circuit_for_backend(
            provider_name, backend_name, n_rounds)

        alg_result = self.run_circuit_on_backend(qc, backend, shots)
        if self.nwr_mode == BruteforceISDCircuit.NWR_BENES:
            if alg_result.accuracy < 0.4:
                n_rounds = n_rounds + 1
                # Rerun the circuit w/ the maximum number of rounds computed
                # by the n_func_domain
                qc, backend, rounds = self.prepare_circuit_for_backend(
                    provider_name, backend_name, n_rounds)
                alg_result = self.run_circuit_on_backend(qc, backend, shots)
            else:
                alg_result.rounds = n_rounds
        else:
            alg_result.rounds = rounds
        return alg_result
