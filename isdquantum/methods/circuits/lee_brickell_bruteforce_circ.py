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


class LeeBrickellCircuit(ISDAbstractCircuit):

    # mct stands for qiskit aqua multicontrol
    # nwr stands for n bits of weight r
    # nwr int is the number of qubits we want to be set to 1. F.e. if it's 1, we want
    # that just 1 over n qubits is set to 1. This is equal the weight w for bruteforce,
    # while w - p for lee_brickell
    # Lee brickell expexts a v in RREF
    def __init__(self, v, syndrome, w, p, need_measures, mct_mode, nwr_mode):
        super().__init__(need_measures, mct_mode, nwr_mode)
        assert w > 0, "Weight must be positive"
        assert p >= 0, "p must be non negative"
        assert p <= w, "p must be less than or equal to weight"
        self.p = p
        self.w = w
        self.r = v.shape[0]
        self.k = v.shape[1]
        assert syndrome.shape[0] == self.r, "Syndrome should be of length r"
        self.v = v
        self.syndrome = syndrome
        _logger.info("k: {}, r: {}, w: {}, p: {}, syndrome: {}".format(
            self.k, self.r, self.w, self.p, self.syndrome))
        self._initialize_circuit()

    def _initialize_circuit(self):
        """
        Initialize the circuit with n qubits. The n is the same n of the H parity matrix and it is used to represent the choice of the column of the matrix.

        :param n: The number of qubits
        :returns: the quantum circuit and the selectors_q register
        :rtype:

        """
        # Global: circuit, ancillas_list, inversion_qubits, n_func_domain, to_measure
        # Private: all other qubits and vars
        self.ancillas_list = []
        self.circuit = QuantumCircuit(
            name="lee_k{0}_r{1}_w{2}_p{3}_{4}_{5}".format(
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
            # TODO check
            # The input domain is nCr(n_lines, p)
            # self.n_func_domain = factorial(len(self.selectors_q)) / factorial(
            #     self.p) / factorial(len(self.selectors_q) - self.p)
            self.n_func_domain = len(self.benes_flip_q)
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
            self.fpc_eq_q = QuantumRegister(1, 'feq')
            self.n_func_domain = 2**len(self.selectors_q)
            self.circuit.add_register(self.selectors_q)
            self.circuit.add_register(self.fpc_cout_q)
            self.circuit.add_register(self.fpc_eq_q)
            self.inversion_about_zero_qubits = self.selectors_q
            qubits_involved_in_multicontrols.append(
                len(self.fpc_dict['results']))

        # We should implement a check on n if it's not a power of 2
        # TODO test if it works
        # if len(self.selectors_q) != self.k:
        #     raise Exception("A.T.M. we can't have less registers")

        qubits_involved_in_multicontrols.append(
            len(self.inversion_about_zero_qubits[1:]))

        self.lee_fpc_dict = hwc.get_circuit_for_qubits_weight_get_pattern(
            self.r)
        self.sum_q = QuantumRegister(self.lee_fpc_dict['n_lines'], 'sum')

        lee_cin_q = QuantumRegister(1, 'lcin')
        self.ancillas_list.append(lee_cin_q[0])

        self.lee_cout_q = QuantumRegister(self.lee_fpc_dict['n_couts'],
                                          'lcout')
        self.lee_eq_q = QuantumRegister(1, 'leq')
        self.circuit.add_register(self.sum_q)
        self.circuit.add_register(lee_cin_q)
        self.circuit.add_register(self.lee_cout_q)
        self.circuit.add_register(self.lee_eq_q)
        qubits_involved_in_multicontrols.append(
            len(self.lee_fpc_dict['results']))

        if self.mct_mode == self.MCT_ADVANCED:
            if len(self.ancillas_list) < 1:
                mct_anc = QuantumRegister(1, 'mctAnc')
                self.circuit.add_register(mct_anc)
                self.ancillas_list.append(mct_anc[0])
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
            # self.mct_anc = None
            pass

        self.to_measure = self.selectors_q

    def _hamming_weight_selectors_check(self):
        _logger.debug("Here")
        self.circuit.barrier()
        self.fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check(
            self.circuit, self.selectors_q, self.ancillas_list,
            self.fpc_cout_q, self.fpc_eq_q, self.ancillas_list, self.p,
            self.fpc_dict, self.mct_mode)
        _logger.debug(
            "Result qubits for Hamming Weight of selectors {}".format(
                self.fpc_result_qubits))
        self.circuit.barrier()

    def _hamming_weight_selectors_check_i(self):
        _logger.debug("Here")
        _logger.debug(
            "Result qubits for Hamming Weight inverse of selectors {}".format(
                self.fpc_result_qubits))
        # TEST_ONLY uncomputeEq should be True, here it's just used for test
        self.fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check_i(
            self.circuit,
            self.selectors_q,
            self.ancillas_list,
            self.fpc_cout_q,
            self.fpc_eq_q,
            self.ancillas_list,
            self.p,
            self.fpc_dict,
            self.fpc_result_qubits,
            self.mct_mode,
            uncomputeEq=True)

    def _matrix2gates(self):
        _logger.debug("Here")
        self.circuit.barrier()
        for i in range(self.v.shape[1]):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.v[:, i].tolist(), self.sum_q, [self.selectors_q[i]], None,
                self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _matrix2gates_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        for i in reversed(range(self.v.shape[1])):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self.v[:, i].tolist(), self.sum_q, [self.selectors_q[i]], None,
                self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _syndrome2gates(self):
        _logger.debug("Here")
        self.circuit.barrier()
        qregs.initialize_qureg_given_bitstring(self.syndrome.tolist(),
                                               self.sum_q, self.circuit)
        self.circuit.barrier()

    def _syndrome2gates_i(self):
        _logger.debug("Here")
        return self._syndrome2gates()

    def _lee_weight_check(self):
        _logger.debug("Here")
        self.circuit.barrier()
        self.lee_result_qubits = hwc.get_circuit_for_qubits_weight_check(
            self.circuit, self.sum_q, self.ancillas_list, self.lee_cout_q,
            self.lee_eq_q, self.ancillas_list, self.w - self.p,
            self.lee_fpc_dict, self.mct_mode)
        _logger.debug("Result qubits for lee weight check are {}".format(
            self.lee_result_qubits))
        self.circuit.barrier()

    def _lee_weight_check_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        # TEST_ONLY uncomputeEq should be True, here it's just used for test
        hwc.get_circuit_for_qubits_weight_check_i(
            self.circuit,
            self.sum_q,
            self.ancillas_list,
            self.lee_cout_q,
            self.lee_eq_q,
            self.ancillas_list,
            self.w - self.p,
            self.lee_fpc_dict,
            self.lee_result_qubits,
            self.mct_mode,
            uncomputeEq=True)
        self.circuit.barrier()

    def _flip_correct_state(self):
        _logger.debug("Here")
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            self.circuit.z(self.lee_eq_q)
        elif self.nwr_mode == self.NWR_FPC:
            # The idea here is that, instead of having another qubits which is set
            # iff both fpc_eq and lee_eq are set and then do a Z gate on this
            # additional qubit, we can just do a CZ gate b/w fpc_eq and lee_eq
            # bcz a Z gate won't do anything to state 0
            self.circuit.cz(self.fpc_eq_q, self.lee_eq_q)
        self.circuit.barrier()

    def prepare_input(self):
        _logger.debug("Here")
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            self.circuit.h(self.benes_flip_q)
            hwg.generate_qubits_with_given_weight_benes(
                self.circuit, self.selectors_q, self.benes_flip_q,
                self.benes_dict)
        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.h(self.selectors_q)
        self.circuit.barrier()

    def prepare_input_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            hwg.generate_qubits_with_given_weight_benes_i(
                self.circuit, self.selectors_q, self.benes_flip_q,
                self.benes_dict)
            self.circuit.h(self.benes_flip_q)
        elif self.nwr_mode == self.NWR_FPC:
            self.circuit.h(self.selectors_q)
        self.circuit.barrier()

    def oracle(self):
        _logger.debug("Here")
        if self.nwr_mode == self.NWR_BENES:
            self._matrix2gates()
            self._syndrome2gates()
            self._lee_weight_check()
            self._flip_correct_state()
            self._lee_weight_check_i()
            self._syndrome2gates_i()
            self._matrix2gates_i()
        elif self.nwr_mode == self.NWR_FPC:
            self._matrix2gates()
            self._syndrome2gates()
            self._hamming_weight_selectors_check()
            self._lee_weight_check()
            self._flip_correct_state()
            self._lee_weight_check_i()
            self._hamming_weight_selectors_check_i()
            self._syndrome2gates_i()
            self._matrix2gates_i()
