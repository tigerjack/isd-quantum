import logging

_logger = logging.getLogger(__name__)


class PrangeISD():
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

        # TODO CEIL + 1 to support everything
        from math import log, ceil
        flips_counter = int(log(self.n, 2)) * int(self.n / 2)
        _logger.debug("Number of hadamard qubits is {0}".format(flips_counter))
        self.flip_q = QuantumRegister(flips_counter, "flip")
        self.circuit.add_register(self.selectors_q)
        self.circuit.add_register(self.sum_q)
        self.circuit.add_register(self.flip_q)

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

    def _n_choose_w(self):
        """
        Given the n selectors_q QuantumRegister, initialize w qubits to 1. w is the weight of the error.

        :param circuit: the quantum circuit
        :param selectors_q: the QuantumRegister representing the n columns selectors
        :param w: the error weight
        :returns: None

        """
        _logger.debug("initializing {0} selectors qubits to 1".format(self.w))
        # Initialize 2 bits to 1, all the others to 0
        for i in range(self.w):
            self.circuit.x(self.selectors_q[i])

    def _permutation(self):
        ancilla_used = 0

        # Hadamard all ancillas
        self.circuit.h(self.flip_q)
        self.circuit.barrier()
        self._permutation_support(ancilla_used, 0, self.n, int(self.n / 2))
        self.circuit.barrier()

    def _permutation_support(self, ancilla_used, start, end, swap_step):
        _logger.debug("Start: {0}, end: {1}, swap_step: {2}".format(
            start, end, swap_step))
        if (swap_step == 0 or start >= end):
            _logger.debug("Base case recursion")
            return ancilla_used
        for i in range(start, int((start + end) / 2)):
            _logger.debug("Cswapping {0} & {1} using hadamard {2}".format(
                i, i + swap_step, ancilla_used))
            self.circuit.cswap(self.flip_q[ancilla_used], self.selectors_q[i],
                               self.selectors_q[i + swap_step])
            ancilla_used += 1
        _logger.debug("Ancilla used after FOR {0}".format(ancilla_used))
        ancilla_used = self._permutation_support(ancilla_used, start,
                                                 int((start + end) / 2),
                                                 int(swap_step / 2))
        _logger.debug(
            "Ancilla used after FIRST recursion {0}".format(ancilla_used))
        ancilla_used = self._permutation_support(ancilla_used,
                                                 int((start + end) / 2), end,
                                                 int(swap_step / 2))
        _logger.debug(
            "Ancilla used after SECOND recursion {0}".format(ancilla_used))
        return ancilla_used

    def _permutation_i(self):
        ancilla_counter = len(self.flip_q)
        _logger.debug(
            "Number of hadamard qubits is {0}".format(ancilla_counter))

        self._permutation_support_i(ancilla_counter - 1, 0, self.n,
                                    int(self.n / 2))
        self.circuit.barrier()
        # Hadamard all ancillas
        self.circuit.h(self.flip_q)
        self.circuit.barrier()

    def _permutation_support_i(self, ancilla_used, start, end, swap_step):
        _logger.debug("Start: {0}, end: {1}, swap_step: {2}".format(
            start, end, swap_step))
        if (swap_step == 0 or start >= end):
            _logger.debug("Base case recursion")
            return ancilla_used
        ancilla_used = self._permutation_support_i(ancilla_used,
                                                   int((start + end) / 2), end,
                                                   int(swap_step / 2))
        _logger.debug(
            "Ancilla used after FIRST recursion {0}".format(ancilla_used))
        ancilla_used = self._permutation_support_i(ancilla_used, start,
                                                   int((start + end) / 2),
                                                   int(swap_step / 2))
        _logger.debug(
            "Ancilla used after SECOND recursion {0}".format(ancilla_used))
        for i in range(int((start + end) / 2) - 1, start - 1, -1):
            _logger.debug("Cswapping {0} & {1} using hadamard {2}".format(
                i, i + swap_step, ancilla_used))
            self.circuit.cswap(self.flip_q[ancilla_used], self.selectors_q[i],
                               self.selectors_q[i + swap_step])
            ancilla_used -= 1
        _logger.debug("Ancilla used after FOR {0}".format(ancilla_used))
        return ancilla_used

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
        self._n_choose_w()
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
            self._n_choose_w()

            self._negate_for_inversion(self.flip_q)
            self._inversion_about_zero(self.flip_q[1:], self.flip_q[0])
            self._negate_for_inversion(self.flip_q)

            self._n_choose_w()
            self._permutation()

        if self.need_measures:
            from qiskit import ClassicalRegister
            cr = ClassicalRegister(self.n, 'cols')
            self.circuit.add_register(cr)
            self.circuit.measure(self.selectors_q, cr)
        return self.circuit
