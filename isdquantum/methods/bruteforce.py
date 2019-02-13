import logging

_logger = logging.getLogger(__name__)


class BruteforceISD():
    def __init__(self, h, syndrome, w, need_measures, mct_mode):
        self.h = h
        self.syndrome = syndrome
        self.w = w
        self.n = h.shape[1]
        self.r = h.shape[0]
        self.mct_mode = mct_mode
        # mode = 'basic'
        self.need_measures = need_measures
        _logger.info(
            "n: {0}, r: {1}, w: {2}, syndrome: {3}, measures: {4}, mct_mode: {5}"
            .format(self.n, self.r, self.w, self.syndrome, self.need_measures,
                    self.mct_mode))
        # Don't know why but it stops working if put in the import section

    def _initialize_circuit(self):
        """
        Initialize the circuit with n qubits. The n is the same n of the H parity matrix and it is used to represent the choice of the column of the matrix.

        :param n: The number of qubits
        :returns: the quantum circuit and the selectors_q register
        :rtype:

        """
        from qiskit.aqua import utils
        from qiskit import QuantumCircuit
        from qiskit import QuantumRegister, QuantumCircuit
        self.circuit = QuantumCircuit()
        _logger.debug("creating n = {0} qubits for selection".format(self.n))

        self.selectors_q = QuantumRegister(self.n, 'select')
        self.sum_q = QuantumRegister(self.r, 'sum')

        if self.mct_mode == 'advanced':
            self.ancillas_q = QuantumRegister(1, 'ancillas')
            self.circuit.add_register(self.ancillas_q)
        elif self.mct_mode == 'basic':
            self.ancillas_q = QuantumRegister(self.flip_q.size - 2, 'ancillas')
            self.circuit.add_register(self.ancillas_q)
        elif self.mct_mode == 'noancilla':
            # no ancilla to add
            self.ancillas_q = None
            pass
        else:
            raise Exception("Invalid mct mode selected")
        # To compute flip_q size and the permutation pattern
        self._permutation_pattern()
        self.flip_q = QuantumRegister(self.permutation['n_flips'], "flip")

        self.circuit.add_register(self.selectors_q)
        self.circuit.add_register(self.flip_q)
        self.circuit.add_register(self.sum_q)

    def _permutation_pattern(self):
        """
        Compute the permuation pattern.
        Basically, the idea is that we want all the possible combinations of n bits with weight w, i.e.
        n choose w.

        """
        from math import log, ceil
        self.permutation = {}
        steps = ceil(log(self.n, 2))
        self.permutation['n_selectors'] = 2**steps
        self.permutation['swaps_qubits_pattern'] = []
        if (self.w == 0 or self.w == self.permutation['n_selectors']):
            raise Exception("No combination is possible")

        # Given the n selectors_q , we would like to
        # initialize w qubits to 1 and then apply the swap algorithm.
        # In this improved version, we carefully choose how to implement the swap
        # algorithm: we don't need the full swap algorithm at each step, but only
        # the swaps effectively used.
        # Also, to improve the algorithm, if w is greater than half of the selectors,
        # instead of initializing all the w qubits to 1 and then apply the algorithm,
        # we initialize n-w qubits to 1, apply the algorithm and finally negate the
        # result. Indeed (n choose w) == (n chooses (n-w))
        if self.w > self.permutation['n_selectors'] / 2:
            initial_swaps = self.permutation['n_selectors'] - self.w
        else:
            initial_swaps = self.w

        self._permutation_pattern_support(
            0, initial_swaps, int(self.permutation['n_selectors'] / 2), 0)
        self.permutation['n_flips'] = len(
            self.permutation['swaps_qubits_pattern'])
        _logger.debug("Number of hadamard qubits is {0}".format(
            self.permutation['n_flips']))

        if (self.w > self.selectors_q.size / 2):
            self.permutation[
                'to_negate_range'] = self.selectors_q.size - self.w
            self.permutation['negated_permutation'] = True
        else:
            self.permutation['to_negate_range'] = self.w
            self.permutation['negated_permutation'] = False

    def _permutation_pattern_support(self, start, end, swap_step, flip_q_idx):
        _logger.debug("Start: {0}, end: {1}, swap_step: {2}".format(
            start, end, swap_step))
        if (swap_step == 0 or start >= end):
            _logger.debug("Base case recursion")
            return flip_q_idx

        for_iter = 0
        for i in range(start, end):
            for_iter += 1
            _logger.debug("cswap({2}, {0}, {1})".format(
                i, i + swap_step, flip_q_idx))
            self.permutation['swaps_qubits_pattern'].append((flip_q_idx, i,
                                                             i + swap_step))
            flip_q_idx += 1

        for_iter_next = min(for_iter, int(swap_step / 2))
        _logger.debug(
            "Before recursion 1, start: {0}, end: {1}, swap_step: {2}, for_iter_next"
            .format(start, end, swap_step, for_iter_next))
        flip_q_idx = self._permutation_pattern_support(
            start, start + for_iter_next, int(swap_step / 2), flip_q_idx)

        _logger.debug(
            "Before recursion, start: {0}, end: {1}, swap_step: {2}, for_iter_next {3}"
            .format(start, end, swap_step, for_iter_next))
        flip_q_idx = self._permutation_pattern_support(
            start + swap_step, start + swap_step + for_iter_next,
            int(swap_step / 2), flip_q_idx)
        return flip_q_idx

    def _permutation(self):
        self.circuit.barrier()
        self.circuit.h(self.flip_q)
        # The idea is that if the condition is true, we negate the flips and do the combinations
        for i in range(self.permutation['to_negate_range']):
            self.circuit.x(self.selectors_q[i])

        for i in self.permutation['swaps_qubits_pattern']:
            self.circuit.cswap(self.flip_q[i[0]], self.selectors_q[i[1]],
                               self.selectors_q[i[2]])
        if self.permutation['negated_permutation']:
            self.circuit.x(self.selectors_q)
        self.circuit.barrier()

    def _permutation_i(self):
        self.circuit.barrier()
        if self.permutation['negated_permutation']:
            self.circuit.x(self.selectors_q)
        for i in self.permutation['swaps_qubits_pattern'][::-1]:
            self.circuit.cswap(self.flip_q[i[0]], self.selectors_q[i[1]],
                               self.selectors_q[i[2]])
        for i in range(self.permutation['to_negate_range']):
            self.circuit.x(self.selectors_q[i])
        self.circuit.h(self.flip_q)
        self.circuit.barrier()

    def _matrix2gates(self):
        for i in range(self.n):
            for j in range(self.r):
                if self.h[j][i] == 1:
                    self.circuit.cx(self.selectors_q[i], self.sum_q[j])
            self.circuit.barrier()

    def _matrix2gates_i(self):
        for i in range(self.n - 1, -1, -1):
            for j in range(self.r - 1, -1, -1):
                if self.h[j][i] == 1:
                    self.circuit.cx(self.selectors_q[i], self.sum_q[j])
            self.circuit.barrier()

    def _syndrome2gates(self):
        for i in range(len(self.syndrome)):
            if (self.syndrome[i] == 0):
                self.circuit.x(self.sum_q[i])
        self.circuit.barrier()

    def _syndrome2gates_i(self):
        return self._syndrome2gates(qc, sum_q, s)

    def _oracle(self, controls_q, to_invert_q):
        # if (ancillas_q is None or ancillas_q.size == 0):
        #     m = 'noancilla'
        #     _logger.debug("oracle -> no ancilla mode for mct")
        # elif (ancillas_q.size == len(sum_q.size) - 2):
        #     m = 'basic'
        #     _logger.debug("oracle -> basic mode for mct")
        # elif (ancillas_q.size == 1):
        #     m = 'advanced'
        #     _logger.debug("oracle -> advanced mode for mct")
        # else:
        #     raise "oracle -> wrong number of ancillas for whatever mode {0}".format(
        #         len(ancillas_q))

        # A CZ obtained by H CX H
        self.circuit.h(to_invert_q)
        self.circuit.mct(
            controls_q, to_invert_q, self.ancillas_q, mode=self.mct_mode)
        self.circuit.h(to_invert_q)

    def _negate_for_inversion(self, *registers):
        for register in registers:
            self.circuit.x(register)

    # single control sum is not a QuantumRegister, but a qubit
    def _inversion_about_zero(self, control_q, multi_control_target_qubit):
        self.circuit.barrier()
        # if (ancillas_q is None or ancillas_q.size == 0):
        #     m = 'noancilla'
        #     _logger.debug("inversion_about_zero -> no ancilla mode for mct")
        # elif (ancillas_q.size == len(control_q) - 2):
        #     m = 'basic'
        #     _logger.debug("inversion_about_zero -> basic mode for mct")
        # elif (ancillas_q.size == 1):
        #     m = 'advanced'
        #     _logger.debug("inversion_about_zero -> advanced mode for mct")
        # else:
        #     raise "inversion_about_zero -> wrong number of ancillas for whatever mode {0}".format(
        #         len(ancillas_q))

        self.circuit.h(multi_control_target_qubit)
        self.circuit.mct(
            control_q,
            multi_control_target_qubit,
            self.ancillas_q,
            mode=self.mct_mode)
        self.circuit.h(multi_control_target_qubit)
        self.circuit.barrier()

    def build_circuit(self):
        self._initialize_circuit()
        self._permutation()

        # Number of grover iterations
        from math import sqrt, pi
        rounds = int(round((pi / 2 * sqrt(self.n) - 1) / 2)) + 1
        _logger.debug("{0} rounds required".format(rounds - 1))
        for i in range(rounds - 1):
            _logger.debug("ITERATION {0}".format(i))
            self._matrix2gates()
            self._syndrome2gates()

            self._oracle(self.sum_q[1:], self.sum_q[0])
            self._syndrome2gates()
            self._matrix2gates_i()
            self._permutation_i()

            self._negate_for_inversion(self.flip_q)
            self._inversion_about_zero(self.flip_q[1:], self.flip_q[0])
            self._negate_for_inversion(self.flip_q)

            self._permutation()

        if self.need_measures:
            from qiskit import ClassicalRegister
            cr = ClassicalRegister(self.n, 'cols')
            self.circuit.add_register(cr)
            self.circuit.measure(self.selectors_q, cr)
        return self.circuit
