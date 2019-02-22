import logging
from isdquantum.methods.circuits.abstract_circ import ISDAbstractCircuit
from isdquantum.circuit import qregs_init as qregs
from isdquantum.circuit import hamming_weight_generate as hwg
from isdquantum.circuit import hamming_weight_compute as hwc
from qiskit.aqua import utils
from qiskit import QuantumCircuit
from qiskit import QuantumRegister, QuantumCircuit
from math import sqrt, pi, asin

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
        # TODO Unneeded h and n for this algorithm, maybe delete from __init__
        # and modify super class
        del self.h
        del self.n
        assert p >= 0, "p must be non negative"
        assert p <= w, "p must be less than or equal to weight"
        assert v.shape[0] == self.r and v.shape[
            1] == self.k, "V must be an rxk Matrix"
        self.p = p
        self.mct_mode = mct_mode
        self.nwr_mode = nwr_mode
        self.v = v
        _logger.info(
            "k: {}, r: {}, w: {}, p: {}, syndrome: {}, measures: {}, mct_mode: {}, nwr_mode: {}"
            .format(self.k, self.r, self.w, self.p, self.syndrome,
                    self.need_measures, self.mct_mode, self.nwr_mode))
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
            name="isd_lee_k{0}_r{1}_w{2}_p{3}_{4}_{5}".format(
                self.k, self.r, self.w, self.p, self.mct_mode, self.nwr_mode))
        qubits_involved_in_multicontrols = []
        if self.nwr_mode == self.NWR_BENES:
            # To compute benes_flip_q size and the permutation pattern
            self.benes_dict = hwg.generate_qubits_with_given_weight_benes_get_pattern(
                self.k, self.p)

            # We don't use only n qubits, but the nearest power of 2
            self.selectors_q = QuantumRegister(self.benes_dict['n_lines'],
                                               'select')
            self.benes_flip_q = QuantumRegister(self.benes_dict['n_flips'],
                                                "bflip")
            self.n_func_domain = len(self.benes_flip_q) + self.w
            self.circuit.add_register(self.selectors_q)
            self.circuit.add_register(self.benes_flip_q)
            self.inversion_about_zero_qubits = self.benes_flip_q
        elif self.nwr_mode == self.NWR_FPC:
            self.fpc_dict = hwc.get_circuit_for_qubits_weight_get_pattern(
                self.k)
            self.selectors_q = QuantumRegister(self.fpc_dict['n_lines'],
                                               'select')
            self.fpc_cout_q = QuantumRegister(self.fpc_dict['n_couts'],
                                              'fcout')
            self.fpc_cin_q = QuantumRegister(1, 'fcin')
            self.fpc_eq_q = QuantumRegister(1, 'feq')
            self.fpc_two_eq_q = QuantumRegister(1, 'f2eq')
            self.n_func_domain = 2**len(self.selectors_q)
            self.circuit.add_register(self.fpc_cin_q)
            self.circuit.add_register(self.selectors_q)
            self.circuit.add_register(self.fpc_cout_q)
            self.circuit.add_register(self.fpc_eq_q)
            self.circuit.add_register(self.fpc_two_eq_q)
            self.inversion_about_zero_qubits = self.selectors_q
            qubits_involved_in_multicontrols.append(
                len(self.fpc_dict['results']))

        # We should implement a check on n if it's not a power of 2
        if len(self.selectors_q) != self.k:
            raise Exception("A.T.M. we can't have less registers")

        qubits_involved_in_multicontrols.append(
            len(self.inversion_about_zero_qubits[1:]))

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
        qubits_involved_in_multicontrols.append(
            len(self.lee_fpc_dict['results']))

        if self.mct_mode == self.MCT_ADVANCED:
            self.mct_anc = QuantumRegister(1, 'mctAnc')
            self.circuit.add_register(self.mct_anc)
        elif self.mct_mode == self.MCT_BASIC:
            _logger.debug("qubits involved in multicontrols are {}".format(
                qubits_involved_in_multicontrols))
            self.mct_anc = QuantumRegister(
                max(qubits_involved_in_multicontrols) - 2, 'mctAnc')
            self.circuit.add_register(self.mct_anc)
        elif self.mct_mode == self.MCT_NOANCILLA:
            self.mct_anc = None

    def _hamming_weight(self):
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            self.circuit.h(self.benes_flip_q)
            hwg.generate_qubits_with_given_weight_benes(
                self.circuit, self.selectors_q, self.benes_flip_q,
                self.benes_dict)
        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.barrier()
            self.fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check(
                self.circuit, self.selectors_q, self.fpc_cin_q,
                self.fpc_cout_q, self.fpc_eq_q, self.mct_anc, self.p,
                self.fpc_dict, self.mct_mode)
            _logger.debug(
                "Result qubits for Hamming Weight of selectors {}".format(
                    self.fpc_result_qubits))
        self.circuit.barrier()

    def _hamming_weight_i(self):
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            hwg.generate_qubits_with_given_weight_benes_i(
                self.circuit, self.selectors_q, self.benes_flip_q,
                self.benes_dict)
            self.circuit.h(self.benes_flip_q)
        elif self.nwr_mode == self.NWR_FPC:
            _logger.debug(
                "Result qubits for Hamming Weight inverse of selectors {}".
                format(self.fpc_result_qubits))
            # TODO uncomputeEq should be True, here it's just used for test
            self.fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check_i(
                self.circuit,
                self.selectors_q,
                self.fpc_cin_q,
                self.fpc_cout_q,
                self.fpc_eq_q,
                self.mct_anc,
                self.p,
                self.fpc_dict,
                self.fpc_result_qubits,
                self.mct_mode,
                uncomputeEq=True)
            self.circuit.barrier()
        self.circuit.barrier()

    def _matrix2gates(self):
        self.circuit.barrier()
        for i in range(self.v.shape[1]):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.v[:, i].tolist(), self.sum_q, [self.selectors_q[i]], None,
                self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _matrix2gates_i(self):
        self.circuit.barrier()
        for i in reversed(range(self.v.shape[1])):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.v[:, i].tolist(), self.sum_q, [self.selectors_q[i]], None,
                self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _syndrome2gates(self):
        self.circuit.barrier()
        qregs.initialize_qureg_given_bitstring(self.syndrome.tolist(),
                                               self.sum_q, self.circuit)
        self.circuit.barrier()

    def _syndrome2gates_i(self):
        return self._syndrome2gates()

    def _lee_weight_check(self):
        self.circuit.barrier()
        self.lee_result_qubits = hwc.get_circuit_for_qubits_weight_check(
            self.circuit, self.sum_q, self.lee_cin_q, self.lee_cout_q,
            self.lee_eq_q, self.mct_anc, self.w - self.p, self.lee_fpc_dict,
            self.mct_mode)
        _logger.debug("Result qubits for lee weight check are {}".format(
            self.lee_result_qubits))
        self.circuit.barrier()

    def _lee_weight_check_i(self):
        self.circuit.barrier()
        # TODO uncomputeEq should be True, here it's just used for test
        hwc.get_circuit_for_qubits_weight_check_i(
            self.circuit,
            self.sum_q,
            self.lee_cin_q,
            self.lee_cout_q,
            self.lee_eq_q,
            self.mct_anc,
            self.w - self.p,
            self.lee_fpc_dict,
            self.lee_result_qubits,
            self.mct_mode,
            uncomputeEq=True)
        self.circuit.barrier()

    def _oracle(self):
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            self.circuit.z(self.lee_eq_q)
        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.ccx(self.fpc_eq_q, self.lee_eq_q, self.fpc_two_eq_q)
            self.circuit.z(self.fpc_two_eq_q)
            self.circuit.ccx(self.fpc_eq_q, self.lee_eq_q, self.fpc_two_eq_q)
        self.circuit.barrier()

    def _inversion_about_zero(self):
        self.circuit.barrier()
        self.circuit.x(self.inversion_about_zero_qubits)

        # CZ = H CX H
        self.circuit.h(self.inversion_about_zero_qubits[0])
        self.circuit.mct(
            self.inversion_about_zero_qubits[1:],
            self.inversion_about_zero_qubits[0],
            self.mct_anc,
            mode=self.mct_mode)
        self.circuit.h(self.inversion_about_zero_qubits[0])
        # CZ END

        self.circuit.x(self.inversion_about_zero_qubits)
        self.circuit.barrier()

    def build_circuit(self):
        self._initialize_circuit()

        # Number of grover iterations
        rounds = pi / (4 * asin(1 / sqrt(self.n_func_domain))) - 1 / 2
        _logger.debug("{0} rounds formally required".format(rounds))
        rounds = max(round(rounds), 1)
        _logger.debug("{0} rounds required".format(rounds))
        if self.nwr_mode == self.NWR_BENES:
            self._hamming_weight()
            for i in range(rounds):
                _logger.debug("ITERATION {0}".format(i))
                self._matrix2gates()
                self._syndrome2gates()
                self._lee_weight_check()
                self._oracle()
                self._lee_weight_check_i()
                # # TODO break put here for a test
                # break
                self._syndrome2gates_i()
                self._matrix2gates_i()

                self._hamming_weight_i()
                # # TODO break put here for a test
                # break
                self._inversion_about_zero()
                self._hamming_weight()

        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.h(self.selectors_q)
            for i in range(rounds):
                self._matrix2gates()
                self._syndrome2gates()
                self._hamming_weight()
                self._lee_weight_check()
                self._oracle()
                self._lee_weight_check_i()
                self._hamming_weight_i()
                self._syndrome2gates_i()
                self._matrix2gates_i()

                self.circuit.h(self.selectors_q)
                self._inversion_about_zero()
                self.circuit.h(self.selectors_q)

        if self.need_measures:
            from qiskit import ClassicalRegister
            to_measure = self.selectors_q
            cr = ClassicalRegister(len(to_measure), 'cols')
            self.circuit.add_register(cr)
            self.circuit.measure(to_measure, cr)
            # TODO just useful for tests to see the status of the registers
            # at the various stages
            # to_measure_2 = self.sum_q
            # cr2 = ClassicalRegister(len(to_measure_2))
            # self.circuit.add_register(cr2)
            # self.circuit.measure(to_measure_2, cr2)
            # to_measure_3 = self.lee_eq_q
            # cr3 = ClassicalRegister(len(to_measure_3))
            # self.circuit.add_register(cr3)
            # self.circuit.measure(to_measure_3, cr3)
            # if self.nwr_mode == 'benes':
            #     to_measure_4 = self.benes_flip_q
            #     cr4 = ClassicalRegister(len(to_measure_4))
            #     self.circuit.add_register(cr4)
            #     self.circuit.measure(to_measure_4, cr4)
            # elif self.nwr_mode == 'fpc':
            #     to_measure_4 = self.fpc_eq_q
            #     to_measure_5 = self.fpc_two_eq_q
            #     cr4 = ClassicalRegister(len(to_measure_4))
            #     self.circuit.add_register(cr4)
            #     self.circuit.measure(to_measure_4, cr4)
            #     cr5 = ClassicalRegister(len(to_measure_5))
            #     self.circuit.add_register(cr5)
            #     self.circuit.measure(to_measure_5, cr5)

        return self.circuit
