import logging
from isdquantum.utils import qregs
from isdquantum.utils import hamming_weight_generate as hwg
from isdquantum.utils import hamming_weight_compute as hwc

_logger = logging.getLogger(__name__)


class BruteforceISD():
    def __init__(self, h, syndrome, w, need_measures, mct_mode):
        self.h = h
        self.syndrome = syndrome
        self.w = w
        self.n = h.shape[1]
        self.r = h.shape[0]
        self.mct_mode = mct_mode
        self.need_measures = need_measures
        _logger.info(
            "n: {0}, r: {1}, w: {2}, syndrome: {3}, measures: {4}, mct_mode: {5}"
            .format(self.n, self.r, self.w, self.syndrome, self.need_measures,
                    self.mct_mode))
        if mct_mode not in ('noancilla', 'basic', 'advanced'):
            raise Exception("Invalid mct_mode selected")

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
        self.circuit = QuantumCircuit(name="isd_{0}_{1}_{2}_{3}".format(
            self.n, self.r, self.w, self.mct_mode))
        # To compute ncr_flip_q size and the permutation pattern
        self.ncr_benes_dict = hwg.generate_qubits_with_given_weight_benes_get_pattern(
            self.n, self.w)

        # We don't use only n qubits, but the nearest power of 2
        self.selectors_q = QuantumRegister(self.ncr_benes_dict['n_lines'],
                                           'select')
        self.ncr_flip_q = QuantumRegister(self.ncr_benes_dict['n_flips'],
                                          "flip")
        self.circuit.add_register(self.selectors_q)
        self.circuit.add_register(self.ncr_flip_q)

        self.sum_q = QuantumRegister(self.r, 'sum')
        self.circuit.add_register(self.sum_q)

        if self.mct_mode == 'advanced':
            self.mct_anc = QuantumRegister(1, 'mctAnc')
            self.circuit.add_register(self.mct_anc)
        elif self.mct_mode == 'basic':
            self.mct_anc = QuantumRegister(self.ncr_flip_q.size - 2, 'mctAnc')
            self.circuit.add_register(self.mct_anc)
        elif self.mct_mode == 'noancilla':
            # no ancilla to add
            self.mct_anc = None
            pass

    def _ncr(self):
        self.circuit.barrier()
        self._ncr_benes()
        self.circuit.barrier()

    def _ncr_i(self):
        self.circuit.barrier()
        self._ncr_benes_i()
        self.circuit.barrier()

    def _ncr_benes(self):
        self.circuit.h(self.ncr_flip_q)
        hwg.generate_qubits_with_given_weight_benes(
            self.circuit, self.selectors_q, self.ncr_flip_q,
            self.ncr_benes_dict)

    def _ncr_benes_i(self):
        hwg.generate_qubits_with_given_weight_benes_i(
            self.circuit, self.selectors_q, self.ncr_flip_q,
            self.ncr_benes_dict)
        self.circuit.h(self.ncr_flip_q)

    def _matrix2gates(self):
        self.circuit.barrier()
        for i in range(self.n):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.h[:, i][::-1].tolist(), self.sum_q, [self.selectors_q[i]],
                None, self.circuit, 'advanced')
        self.circuit.barrier()

    def _matrix2gates_i(self):
        self.circuit.barrier()
        for i in reversed(range(self.n)):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.h[:, i][::-1].tolist(), self.sum_q, [self.selectors_q[i]],
                None, self.circuit, 'advanced')
        self.circuit.barrier()

    def _syndrome2gates(self):
        self.circuit.barrier()
        for i in range(len(self.syndrome)):
            if (self.syndrome[i] == 0):
                self.circuit.x(self.sum_q[i])
        self.circuit.barrier()

    def _syndrome2gates_i(self):
        return self._syndrome2gates(qc, sum_q, s)

    def _oracle(self):
        self.circuit.barrier()
        controls_q = self.sum_q[1:]
        to_invert_q = self.sum_q[0]
        # A CZ obtained by H CX H
        self.circuit.h(to_invert_q)
        self.circuit.mct(
            controls_q, to_invert_q, self.mct_anc, mode=self.mct_mode)
        self.circuit.h(to_invert_q)
        self.circuit.barrier()

    def _negate_for_inversion(self):
        self.circuit.barrier()
        to_negate_registers = self.ncr_flip_q
        for register in to_negate_registers:
            self.circuit.x(register)
        self.circuit.barrier()

    def _inversion_about_zero(self):
        self.circuit.barrier()
        #TODO
        control_q = self.ncr_flip_q[1:]
        multi_control_target_qubit = self.ncr_flip_q[0]

        # CZ = H CX H
        self.circuit.h(multi_control_target_qubit)
        self.circuit.mct(
            control_q,
            multi_control_target_qubit,
            self.mct_anc,
            mode=self.mct_mode)
        self.circuit.h(multi_control_target_qubit)
        self.circuit.barrier()

    def build_circuit(self):
        self._initialize_circuit()
        self._ncr()

        # Number of grover iterations
        from math import sqrt, pi
        rounds = int(round((pi / 2 * sqrt(self.n) - 1) / 2)) + 1
        _logger.debug("{0} rounds required".format(rounds - 1))
        for i in range(rounds - 1):
            _logger.debug("ITERATION {0}".format(i))
            self._matrix2gates()
            self._syndrome2gates()

            self._oracle()
            self._syndrome2gates()
            self._matrix2gates_i()
            self._ncr_i()

            self._negate_for_inversion()
            self._inversion_about_zero()
            self._negate_for_inversion()

            self._ncr()

        if self.need_measures:
            from qiskit import ClassicalRegister
            cr = ClassicalRegister(self.n, 'cols')
            self.circuit.add_register(cr)
            self.circuit.measure(self.selectors_q, cr)
        return self.circuit
