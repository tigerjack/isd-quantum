import logging
from isdquantum.utils import misc
from isdquantum.methods.circuits.bruteforce_circ import BruteforceISDCircuit
from isdquantum.methods.algorithms.abstract_alg import ISDAbstractAlg

logger = logging.getLogger(__name__)


class BruteforceAlg(ISDAbstractAlg):
    def __init__(self, h, syndrome, w, need_measures, mct_mode, nwr_mode):
        super().__init__(h, syndrome, w, need_measures, mct_mode, nwr_mode)

    def prepare_circuit_for_backend(self, provider_name, backend_name):

        bru_circ = BruteforceISDCircuit(self.h, self.syndrome, self.w,
                                        self.need_measures, self.mct_mode,
                                        self.nwr_mode)
        qc = bru_circ.build_circuit()

        n_qubits = qc.width()
        logger.info("Number of qubits needed = {0}".format(n_qubits))
        backend = misc.get_backend(provider_name, backend_name, n_qubits)
        logger.debug("After function, backend name is {0}".format(
            backend.name()))
        # process_compiled_circuit(args, qc, backend)
        return qc, backend

    def run_circuit_on_backend(self, qc, backend, shots=1024):
        result = misc.run(qc, backend, shots)
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
        return result, error, accuracy

    def run(self, provider_name, backend_name, shots=8192):
        qc, backend = self.prepare_circuit_for_backend(provider_name,
                                                       backend_name)
        result, error, accuracy = self.run_circuit_on_backend(
            qc, backend, shots)
        return qc, result, error, accuracy
