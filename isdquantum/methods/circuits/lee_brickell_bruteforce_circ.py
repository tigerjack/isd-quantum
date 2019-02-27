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
    def __init__(self, v, syndrome, w, p, need_measures, mct_mode, nwr_mode,
                 n_rounds):
        super().__init__(need_measures, mct_mode, nwr_mode, n_rounds)
        assert w > 0, "Weight must be positive"
        assert p >= 0, "p must be non negative"
        assert p <= w, "p must be less than or equal to weight"
        self._p = p
        self._w = w
        self._r = v.shape[0]
        self._k = v.shape[1]
        assert syndrome.shape[0] == self._r, "Syndrome should be of length r"
        self._v = v
        self._syndrome = syndrome
        _logger.info("k: {}, r: {}, w: {}, p: {}, syndrome: {}".format(
            self._k, self._r, self._w, self._p, self._syndrome))
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
                self._k, self._r, self._w, self._p, self.mct_mode,
                self.nwr_mode))
        qubits_involved_in_multicontrols = []
        if self.nwr_mode == self.NWR_BENES:
            # To compute benes_flip_q size and the permutation pattern
            self._benes_dict = hwg.generate_qubits_with_given_weight_benes_get_pattern(
                self._k, self._p)
            if self._benes_dict['n_flips'] <= 1:
                raise Exception("Too few flips, unable to grover")

            # We don't use only n qubits, but the nearest power of 2
            self._selectors_q = QuantumRegister(self._benes_dict['n_lines'],
                                                'select')
            self._benes_flip_q = QuantumRegister(self._benes_dict['n_flips'],
                                                 "bflip")
            # TODO check
            # The input domain is nCr(n_lines, p)
            self.n_func_domain = factorial(len(self._selectors_q)) / factorial(
                self._p) / factorial(len(self._selectors_q) - self._p)
            # self.n_func_domain = len(self._benes_flip_q)
            self.circuit.add_register(self._selectors_q)
            self.circuit.add_register(self._benes_flip_q)
            self.inversion_about_zero_qubits = self._benes_flip_q
        elif self.nwr_mode == self.NWR_FPC:
            self._fpc_dict = hwc.get_circuit_for_qubits_weight_get_pattern(
                self._k)
            self._selectors_q = QuantumRegister(self._fpc_dict['n_lines'],
                                                'select')
            self._fpc_cout_q = QuantumRegister(self._fpc_dict['n_couts'],
                                               'fcout')
            self._fpc_eq_q = QuantumRegister(1, 'feq')
            self.n_func_domain = 2**len(self._selectors_q)
            self.circuit.add_register(self._selectors_q)
            self.circuit.add_register(self._fpc_cout_q)
            self.circuit.add_register(self._fpc_eq_q)
            self.inversion_about_zero_qubits = self._selectors_q
            qubits_involved_in_multicontrols.append(
                len(self._fpc_dict['results']))

        # We should implement a check on n if it's not a power of 2
        # TODO test if it works
        # if len(self._selectors_q) != self._k:
        #     raise Exception("A.T.M. we can't have less registers")

        qubits_involved_in_multicontrols.append(
            len(self.inversion_about_zero_qubits[1:]))

        self._lee_fpc_dict = hwc.get_circuit_for_qubits_weight_get_pattern(
            self._r)
        self._sum_q = QuantumRegister(self._lee_fpc_dict['n_lines'], 'sum')

        lee_cin_q = QuantumRegister(1, 'lcin')
        self.ancillas_list.append(lee_cin_q[0])

        self._lee_cout_q = QuantumRegister(self._lee_fpc_dict['n_couts'],
                                           'lcout')
        self._lee_eq_q = QuantumRegister(1, 'leq')
        self.circuit.add_register(self._sum_q)
        self.circuit.add_register(lee_cin_q)
        self.circuit.add_register(self._lee_cout_q)
        self.circuit.add_register(self._lee_eq_q)
        qubits_involved_in_multicontrols.append(
            len(self._lee_fpc_dict['results']))

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

        self.to_measure = self._selectors_q

    def _hamming_weight_selectors_check(self):
        _logger.debug("Here")
        self.circuit.barrier()
        self._fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check(
            self.circuit, self._selectors_q, self.ancillas_list,
            self._fpc_cout_q, self._fpc_eq_q, self.ancillas_list, self._p,
            self._fpc_dict, self.mct_mode)
        _logger.debug(
            "Result qubits for Hamming Weight of selectors {}".format(
                self._fpc_result_qubits))
        self.circuit.barrier()

    def _hamming_weight_selectors_check_i(self):
        _logger.debug("Here")
        _logger.debug(
            "Result qubits for Hamming Weight inverse of selectors {}".format(
                self._fpc_result_qubits))
        # TEST_ONLY uncomputeEq should be True, here it's just used for test
        self._fpc_result_qubits = hwc.get_circuit_for_qubits_weight_check_i(
            self.circuit,
            self._selectors_q,
            self.ancillas_list,
            self._fpc_cout_q,
            self._fpc_eq_q,
            self.ancillas_list,
            self._p,
            self._fpc_dict,
            self._fpc_result_qubits,
            self.mct_mode,
            uncomputeEq=True)

    def _matrix2gates(self):
        _logger.debug("Here")
        self.circuit.barrier()
        for i in range(self._v.shape[1]):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self._v[:, i].tolist(), self._sum_q, [self._selectors_q[i]],
                None, self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _matrix2gates_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        for i in reversed(range(self._v.shape[1])):
            qregs.conditionally_initialize_qureg_given_bitstring(
                self._v[:, i].tolist(), self._sum_q, [self._selectors_q[i]],
                None, self.circuit, self.mct_mode)
        self.circuit.barrier()

    def _syndrome2gates(self):
        _logger.debug("Here")
        self.circuit.barrier()
        qregs.initialize_qureg_given_bitstring(self._syndrome.tolist(),
                                               self._sum_q, self.circuit)
        self.circuit.barrier()

    def _syndrome2gates_i(self):
        _logger.debug("Here")
        return self._syndrome2gates()

    def _lee_weight_check(self):
        _logger.debug("Here")
        self.circuit.barrier()
        self._lee_result_qubits = hwc.get_circuit_for_qubits_weight_check(
            self.circuit, self._sum_q, self.ancillas_list, self._lee_cout_q,
            self._lee_eq_q, self.ancillas_list, self._w - self._p,
            self._lee_fpc_dict, self.mct_mode)
        _logger.debug("Result qubits for lee weight check are {}".format(
            self._lee_result_qubits))
        self.circuit.barrier()

    def _lee_weight_check_i(self):
        _logger.debug("Here")
        self.circuit.barrier()
        # TEST_ONLY uncomputeEq should be True, here it's just used for test
        hwc.get_circuit_for_qubits_weight_check_i(
            self.circuit,
            self._sum_q,
            self.ancillas_list,
            self._lee_cout_q,
            self._lee_eq_q,
            self.ancillas_list,
            self._w - self._p,
            self._lee_fpc_dict,
            self._lee_result_qubits,
            self.mct_mode,
            uncomputeEq=True)
        self.circuit.barrier()

    def _flip_correct_state(self):
        _logger.debug("Here")
        self.circuit.barrier()
        if self.nwr_mode == self.NWR_BENES:
            self.circuit.z(self._lee_eq_q)
        elif self.nwr_mode == self.NWR_FPC:
            # The idea here is that, instead of having another qubits which is set
            # iff both fpc_eq and lee_eq are set and then do a Z gate on this
            # additional qubit, we can just do a CZ gate b/w fpc_eq and lee_eq
            # bcz a Z gate won't do anything to state 0
            self.circuit.cz(self._fpc_eq_q, self._lee_eq_q)
        self.circuit.barrier()

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
