import logging
from isdquantum.methods.circuits.abstract_circ import ISDAbstractCircuit
from isdquantum.circuit import qregs_init as qregs
from isdquantum.circuit import hamming_weight_generate as hwg
from isdquantum.circuit import hamming_weight_compute as hwc
from qiskit import QuantumCircuit
from qiskit import QuantumRegister, QuantumCircuit
from qiskit.aqua import utils
from math import factorial

_logger = logging.getLogger(__name__)


class BruteforceISDCircuit(ISDAbstractCircuit):

    # mct stands for qiskit aqua multicontrol
    # nwr stands for n bits of weight r
    # In benes mode it could happen that the correct error vector is the one obtained by the sum
    # of the first w columns. This means that all the flip_q hadamards are off and for this reason
    # there is no entanglement. Multiple rounds of the circuits are unneeded and have the only
    # effect to decrease the probability outcome.
    def __init__(self, h, syndrome, w, need_measures, mct_mode, nwr_mode,
                 n_rounds):
        super().__init__(need_measures, mct_mode, nwr_mode, n_rounds)
        assert w > 0, "Weight must be positive"
        self._h = h
        self._w = w
        self._r = h.shape[0]
        self._n = h.shape[1]
        assert syndrome.shape[0] == self._r, "Syndrome should be of length r"
        self._syndrome = syndrome
        _logger.info("n: {0}, r: {1}, w: {2}, syndrome: {3}".format(
            self._n, self._r, self._w, self._syndrome))
        self._initialize_circuit()

    def _initialize_circuit(self):
        """
        Initialize the circuit with n qubits. The n is the same n of the H parity matrix and it is used to represent the choice of the column of the matrix.

        :param n: The number of qubits
        :returns: the quantum circuit and the selectors_q register
        :rtype:

        """
        self.circuit = QuantumCircuit(
            name="bruteforce_{0}_{1}_{2}_{3}_{4}".format(
                self._n, self._r, self._w, self.mct_mode, self.nwr_mode))
        self.sum_q = QuantumRegister(self._r, 'sum')
        self.ancillas_list = []
        qubits_involved_in_multicontrols = []
        if self.nwr_mode == self.NWR_BENES:
            # To compute benes_flip_q size and the permutation pattern
            self._benes_dict = hwg.generate_qubits_with_given_weight_benes_get_pattern(
                self._n, self._w)

            # We don't use only n qubits, but the nearest power of 2
            self._selectors_q = QuantumRegister(self._benes_dict['n_lines'],
                                                'select')
            self._benes_flip_q = QuantumRegister(self._benes_dict['n_flips'],
                                                 "flip")
            # TODO check
            # self.n_func_domain = len(self._benes_flip_q) + self._w
            # self.n_func_domain = len(self._benes_flip_q)
            # The input domain is nCr(n_lines, w)
            self.n_func_domain = factorial(len(self._selectors_q)) / factorial(
                self._w) / factorial(len(self._selectors_q) - self._w)
            self.circuit.add_register(self._selectors_q)
            self.circuit.add_register(self._benes_flip_q)
            self.inversion_about_zero_qubits = self._benes_flip_q
            # Flip right state
            qubits_involved_in_multicontrols.append(len(self.sum_q[1:]))
        elif self.nwr_mode == self.NWR_FPC:
            self._fpc_dict = hwc.get_circuit_for_qubits_weight_get_pattern(
                self._n)
            self._selectors_q = QuantumRegister(self._fpc_dict['n_lines'],
                                                'select')
            self._fpc_cout_q = QuantumRegister(self._fpc_dict['n_couts'],
                                               'cout')
            fpc_cin_q = QuantumRegister(1, 'cin')
            self.ancillas_list.append(fpc_cin_q[0])
            self._fpc_eq_q = QuantumRegister(1, 'eq')
            self.n_func_domain = 2**len(self._selectors_q)
            self.circuit.add_register(fpc_cin_q)
            self.circuit.add_register(self._selectors_q)
            self.circuit.add_register(self._fpc_cout_q)
            self.circuit.add_register(self._fpc_eq_q)
            self.inversion_about_zero_qubits = self._selectors_q
            # For weight check of hwc
            qubits_involved_in_multicontrols.append(
                len(self._fpc_dict['results']))
            # Flip right state
            qubits_involved_in_multicontrols.append(
                len(self.sum_q[1:]) + len(self._fpc_eq_q))

        # We should implement a check on n if it's not a power of 2
        # TODO test if it works
        # if len(self._selectors_q) != self._n:
        #     raise Exception("A.T.M. we can't have less registers")

        # For inversion about zero
        qubits_involved_in_multicontrols.append(
            len(self.inversion_about_zero_qubits[1:]))

        self.circuit.add_register(self.sum_q)

        if self.mct_mode == self.MCT_ADVANCED:
            if len(self.ancillas_list) < 1:
                mct_anc = QuantumRegister(1, 'mctAnc')
                self.ancillas_list.append(mct_anc[0])
                self.circuit.add_register(mct_anc)
        elif self.mct_mode == self.MCT_BASIC:
            _logger.debug("qubits involved in multicontrols are {}".format(
                qubits_involved_in_multicontrols))
            ancilla_needed = (max(qubits_involved_in_multicontrols) - 2) - len(
                self.ancillas_list)
            if ancilla_needed > 0:
                mct_anc = QuantumRegister(ancilla_needed, 'mctAnc')
                self.circuit.add_register(mct_anc)
                self.ancillas_list.extend(mct_anc)
        elif self.mct_mode == self.MCT_NOANCILLA:
            # no ancilla to add
            # self.mct_anc = None
            pass

        self.to_measure = self._selectors_q

    def prepare_input(self):
        _logger.debug("Here")
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            self.circuit.h(self._benes_flip_q)
            hwg.generate_qubits_with_given_weight_benes(
                self.circuit, self._selectors_q, self._benes_flip_q,
                self._benes_dict)
        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.h(self._selectors_q)
        self.circuit.barrier()

    def prepare_input_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            hwg.generate_qubits_with_given_weight_benes_i(
                self.circuit, self._selectors_q, self._benes_flip_q,
                self._benes_dict)
            self.circuit.h(self._benes_flip_q)
        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.h(self._selectors_q)
        self.circuit.barrier()

    def _hamming_weight_selectors_check(self):
        _logger.debug("Here")
        self.circuit.barrier()
        self.fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check(
            self.circuit, self._selectors_q, self.ancillas_list,
            self._fpc_cout_q, self._fpc_eq_q, self.ancillas_list, self._w,
            self._fpc_dict)
        _logger.debug(
            "Result qubits for Hamming Weight of selectors {}".format(
                self.fpc_result_qubits))
        self.circuit.barrier()

    def _hamming_weight_selectors_check_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        self.fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check_i(
            self.circuit,
            self._selectors_q,
            self.ancillas_list,
            self._fpc_cout_q,
            self._fpc_eq_q,
            self.ancillas_list,
            self._w,
            self._fpc_dict,
            self.fpc_result_qubits,
            uncomputeEq=True)
        self.circuit.barrier()

    def _matrix2gates(self):
        _logger.debug("Here")
        self.circuit.barrier()
        for i in range(self._h.shape[1]):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self._h[:, i].tolist(), self.sum_q, [self._selectors_q[i]],
                None, self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _matrix2gates_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        for i in reversed(range(self._h.shape[1])):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self._h[:, i].tolist(), self.sum_q, [self._selectors_q[i]],
                None, self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _syndrome2gates(self):
        _logger.debug("Here")
        self.circuit.barrier()
        qregs.initialize_qureg_to_complement_of_bitarray(
            self._syndrome.tolist(), self.sum_q, self.circuit)
        self.circuit.barrier()

    def _syndrome2gates_i(self):
        return self._syndrome2gates()

    def _flip_correct_state(self):
        _logger.debug("Here")
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            controls_q = self.sum_q[1:]
            to_invert_q = self.sum_q[0]
        elif self.nwr_mode == self.NWR_FPC:
            controls_q = [self._fpc_eq_q[0]] + [qr for qr in self.sum_q[1:]]
            to_invert_q = self.sum_q[0]
        # A CZ obtained by H CX H
        self.circuit.h(to_invert_q)
        self.circuit.mct(
            controls_q, to_invert_q, self.ancillas_list, mode=self.mct_mode)
        self.circuit.h(to_invert_q)
        # CZ END
        self.circuit.barrier()

    def oracle(self):
        _logger.debug("Here")
        if self.nwr_mode == self.NWR_BENES:
            self._matrix2gates()
            self._syndrome2gates()
            self._flip_correct_state()
            self._syndrome2gates_i()
            self._matrix2gates_i()
        elif self.nwr_mode == self.NWR_FPC:
            self._matrix2gates()
            self._syndrome2gates()
            self._hamming_weight_selectors_check()
            self._flip_correct_state()
            self._hamming_weight_selectors_check_i()
            self._syndrome2gates_i()
            self._matrix2gates_i()
