import logging
from isdquantum.methods.circuits.abstract_circ import ISDAbstractCircuit
from isdquantum.circuit import qregs_init as qregs
from isdquantum.circuit import hamming_weight_generate as hwg
from isdquantum.circuit import hamming_weight_compute as hwc
from qiskit.aqua import utils
from qiskit import QuantumCircuit
from qiskit import QuantumRegister, QuantumCircuit

_logger = logging.getLogger(__name__)


class LeeBrickellCircuit(ISDAbstractCircuit):
    NWR_BENES = 'benes'
    NWR_FPC = 'fpc'
    NWR_MODES = (NWR_BENES, NWR_FPC)
    MCT_ADVANCED = 'advanced'
    MCT_BASIC = 'basic'
    MCT_NOANCILLA = 'noancilla'
    MCT_MODES = (MCT_ADVANCED, MCT_BASIC, MCT_NOANCILLA)

    # mct stands for qiskit aqua multicontrol
    # nwr stands for n bits of weight r
    # nwr int is the number of qubits we want to be set to 1. F.e. if it's 1, we want
    # that just 1 over n qubits is set to 1. This is equal the weight w for bruteforce,
    # while w - p for lee_brickell
    # Lee brickell expexts a v in RREF
    def __init__(self, h, v, syndrome, w, p, need_measures, mct_mode,
                 nwr_mode):
        super().__init__(h, syndrome, w, need_measures)
        assert p >= 0, "p must be non negative"
        assert p <= w, "p must be less than or equal to weight"
        assert v.shape[0] == self.r and v.shape[
            1] == self.k, "V must be a kxk Matrix"
        self.p = p
        self.mct_mode = mct_mode
        self.nwr_mode = nwr_mode
        self.lee_int = w - p
        # print(self.lee_int)
        self.v = v
        _logger.info(
            "n: {0}, r: {1}, w: {2}, syndrome: {3}, measures: {4}, mct_mode: {5}"
            .format(self.n, self.r, self.w, self.syndrome, self.need_measures,
                    self.mct_mode))
        if mct_mode not in self.MCT_MODES:
            raise Exception("Invalid mct_mode selected")
        if nwr_mode not in self.NWR_MODES:
            raise Exception("Invalid nwr_mode selected")

    def _initialize_circuit(self):
        """
        Initialize the circuit with n qubits. The n is the same n of the H parity matrix and it is used to represent the choice of the column of the matrix.

        :param n: The number of qubits
        :returns: the quantum circuit and the selectors_q register
        :rtype:

        """
        self.circuit = QuantumCircuit(
            name="isd_lee_n{0}_r{1}_w{2}_p{3}_{4}_{5}".format(
                self.n, self.r, self.w, self.p, self.mct_mode, self.nwr_mode))
        del self.n
        # del self.r
        if self.nwr_mode == self.NWR_BENES:
            # To compute ncr_flip_q size and the permutation pattern
            self.ncr_benes_dict = hwg.generate_qubits_with_given_weight_benes_get_pattern(
                self.k, self.p)

            # We don't use only n qubits, but the nearest power of 2
            self.selectors_q = QuantumRegister(self.ncr_benes_dict['n_lines'],
                                               'select')
            self.ncr_flip_q = QuantumRegister(self.ncr_benes_dict['n_flips'],
                                              "flip")
            self.n_func_domain = len(self.ncr_flip_q) + self.w
            self.circuit.add_register(self.selectors_q)
            self.circuit.add_register(self.ncr_flip_q)
        elif self.nwr_mode == self.NWR_FPC:
            self.fpc_pattern_dict = hwc.get_circuit_for_qubits_weight_get_pattern(
                self.n)
            self.selectors_q = QuantumRegister(
                self.fpc_pattern_dict['n_lines'], 'select')
            self.cout_q = QuantumRegister(self.fpc_pattern_dict['n_couts'],
                                          'cout')
            self.cin_q = QuantumRegister(1, 'cin')
            self.eq_q = QuantumRegister(1, 'eq')
            self.n_func_domain = 2**len(self.selectors_q)
            self.circuit.add_register(self.cin_q)
            self.circuit.add_register(self.selectors_q)
            self.circuit.add_register(self.cout_q)
            self.circuit.add_register(self.eq_q)

        self.lee_fpc_dict = hwc.get_circuit_for_qubits_weight_get_pattern(
            self.r)
        self.sum_q = QuantumRegister(self.lee_fpc_dict['n_lines'], 'sum')
        self.lee_cin_q = QuantumRegister(1, 'lcin')
        self.lee_cout_q = QuantumRegister(self.lee_fpc_dict['n_couts'],
                                          'lcout')
        self.lee_eq_q = QuantumRegister(1, 'leq')
        self.circuit.add_register(self.sum_q)
        self.circuit.add_register(self.lee_cin_q)
        self.circuit.add_register(self.lee_cout_q)
        self.circuit.add_register(self.lee_eq_q)

        if self.mct_mode == self.MCT_ADVANCED:
            self.mct_anc = QuantumRegister(1, 'mctAnc')
            self.circuit.add_register(self.mct_anc)
        elif self.mct_mode == self.MCT_BASIC:
            # TODO
            raise Exception('unstable')
            pass
            self.mct_anc = QuantumRegister(self.ncr_flip_q.size - 2, 'mctAnc')
            self.circuit.add_register(self.mct_anc)
        elif self.mct_mode == self.MCT_NOANCILLA:
            # no ancilla to add
            self.mct_anc = None
            pass
        # We still need 1 ancilla for other parts of the circuit
        if self.mct_anc == None:
            self.mct_anc = QuantumRegister(1, 'mctAnc')
            self.circuit.add_register(self.mct_anc)

    def _hamming_weight(self):
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            self.circuit.h(self.ncr_flip_q)
            hwg.generate_qubits_with_given_weight_benes(
                self.circuit, self.selectors_q, self.ncr_flip_q,
                self.ncr_benes_dict)
        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.barrier()
            self.result_qubits = hwc.get_circuit_for_qubits_weight_check(
                self.circuit, self.selectors_q, self.cin_q, self.cout_q,
                self.eq_q, self.mct_anc, self.w, self.fpc_pattern_dict)
        self.circuit.barrier()

    def _hamming_weight_i(self):
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            hwg.generate_qubits_with_given_weight_benes_i(
                self.circuit, self.selectors_q, self.ncr_flip_q,
                self.ncr_benes_dict)
            self.circuit.h(self.ncr_flip_q)
        elif self.nwr_mode == self.NWR_FPC:
            self.result_qubits = hwc.get_circuit_for_qubits_weight_check_i(
                self.circuit, self.selectors_q, self.cin_q, self.cout_q,
                self.eq_q, self.mct_anc, self.w, self.fpc_pattern_dict,
                self.result_qubits)
            self.circuit.barrier()
        self.circuit.barrier()

    def _matrix2gates(self):
        self.circuit.barrier()
        for i in range(len(self.selectors_q)):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.h[:, i][::-1].tolist(), self.sum_q, [self.selectors_q[i]],
                None, self.circuit, 'advanced')
        self.circuit.barrier()

    def _matrix2gates_i(self):
        self.circuit.barrier()
        for i in reversed(range(len(self.selectors_q))):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.h[:, i][::-1].tolist(), self.sum_q, [self.selectors_q[i]],
                None, self.circuit, 'advanced')
        self.circuit.barrier()

    def _syndrome2gates(self):
        self.circuit.barrier()
        # TODO
        qregs.initialize_qureg_given_bitstring(self.syndrome.tolist()[::-1],
                                               self.sum_q, self.circuit)
        # for i in range(len(self.syndrome)):
        #     if (self.syndrome[i] == 0):
        #         self.circuit.x(self.sum_q[i])
        self.circuit.barrier()

    def _syndrome2gates_i(self):
        return self._syndrome2gates()

    def _lee_weight_check(self):
        self.circuit.barrier()
        self.result_qubits = hwc.get_circuit_for_qubits_weight_check(
            self.circuit, self.sum_q, self.lee_cin_q, self.lee_cout_q,
            self.lee_eq_q, self.mct_anc, self.lee_int, self.lee_fpc_dict)
        print(self.result_qubits)
        self.circuit.barrier()

    def _lee_weight_check_i(self):
        self.circuit.barrier()
        hwc.get_circuit_for_qubits_weight_check_i(
            self.circuit, self.sum_q, self.lee_cin_q, self.lee_cout_q,
            self.lee_eq_q, self.mct_anc, self.lee_int, self.lee_fpc_dict,
            self.result_qubits)
        self.circuit.barrier()

    def _oracle(self):
        if self.nwr_mode == self.NWR_BENES:
            # controls_q = [qr for qr in self.sum_q[1:]] + [self.lee_eq_q[0]]
            controls_q = [self.lee_eq_q[0]]
            to_invert_q = self.sum_q[0]
        elif self.nwr_mode == self.NWR_FPC:
            controls_q = [self.eq_q[0]] + [qr for qr in self.sum_q[1:]]
            to_invert_q = self.sum_q[0]
        # A CZ obtained by H CX H
        self.circuit.barrier()
        self.circuit.h(to_invert_q)
        self.circuit.mct(
            controls_q, to_invert_q, self.mct_anc, mode=self.mct_mode)
        self.circuit.h(to_invert_q)
        self.circuit.barrier()

    def _negate_for_inversion(self):
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            to_negate_registers = self.ncr_flip_q
        elif self.nwr_mode == self.NWR_FPC:
            to_negate_registers = self.selectors_q
        for register in to_negate_registers:
            self.circuit.x(register)
        self.circuit.barrier()

    def _inversion_about_zero(self):
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            control_q = self.ncr_flip_q[1:]
            multi_control_target_qubit = self.ncr_flip_q[0]
        elif self.nwr_mode == self.NWR_FPC:
            control_q = self.selectors_q[1:]
            multi_control_target_qubit = self.selectors_q[0]

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
        # self._hamming_weight()

        # Number of grover iterations
        from math import sqrt, pi, asin
        # TODO check formula
        # rounds = int(round((pi / 2 * sqrt(self.n_hadamards) - 1) / 2)) - 1
        rounds = pi / (4 * asin(1 / sqrt(self.n_func_domain))) - 1 / 2
        print("{0} rounds formally required".format(rounds))
        rounds = max(round(rounds), 1)
        print("{0} rounds required".format(rounds))
        if self.nwr_mode == self.NWR_BENES:
            for i in range(rounds):
                _logger.debug("ITERATION {0}".format(i))
                self._hamming_weight()
                self._matrix2gates()
                self._syndrome2gates()
                self._lee_weight_check()
                # TODO delete, just a test

                self._oracle()
                self._lee_weight_check_i()
                self._syndrome2gates_i()
                self._matrix2gates_i()
                self._hamming_weight_i()

                self._negate_for_inversion()
                self._inversion_about_zero()
                self._negate_for_inversion()

            # self._hamming_weight()
            # TODO uncomment, just a test
            self._hamming_weight()
        elif self.nwr_mode == self.NWR_FPC:
            for i in range(rounds):
                self.circuit.h(self.selectors_q)
                self._syndrome2gates()
                self._matrix2gates()
                self._hamming_weight()
                self._oracle()
                self._hamming_weight_i()
                self._matrix2gates_i()
                self._syndrome2gates()
                self.circuit.h(self.selectors_q)
                # break
                self._negate_for_inversion()
                self._inversion_about_zero()
                self._negate_for_inversion()
            # TODO uncomment, just a test
            self.circuit.h(self.selectors_q)

        if self.need_measures:
            from qiskit import ClassicalRegister
            to_measure = self.selectors_q
            cr = ClassicalRegister(len(to_measure), 'cols')
            self.circuit.add_register(cr)
            self.circuit.measure(to_measure, cr)
            # to_measure_2 = self.lee_eq_q
            # cr2 = ClassicalRegister(len(to_measure_2))
            # self.circuit.add_register(cr2)
            # self.circuit.measure(to_measure_2, cr2)
            # to_measure_3 = self.ncr_flip_q
            # cr3 = ClassicalRegister(len(to_measure_3))
            # self.circuit.add_register(cr3)
            # self.circuit.measure(to_measure_3, cr3)
            # to_measure_4 = self.sum_q
            # cr4 = ClassicalRegister(len(to_measure_4))
            # self.circuit.add_register(cr4)
            # self.circuit.measure(to_measure_4, cr4)
        return self.circuit