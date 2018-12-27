import logging
from math import log, sqrt, pi
from qiskit import QuantumCircuit, QuantumRegister
import composed_gates
import pseudoquantumregister as pse

_logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
_formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
_handler.setFormatter(_formatter)
if (_logger.hasHandlers()):
    _logger.handlers.clear()
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)


def initialize_circuit(n):
    """
    Initialize the circuit with n qubits. The n is the same n of the H parity matrix and it is used to represent the choice of the column of the matrix.

    :param n: The number of qubits
    :returns: the quantum circuit and the selectors_q register
    :rtype:

    """
    _logger.debug(
        "initialize_circuit -> creating n = {0} qubits for selection".format(
            n))
    selectors_q = QuantumRegister(n, 'select')
    circuit = QuantumCircuit(selectors_q)

    return circuit, selectors_q


def n_choose_w(circuit, selectors_q, w):
    """
    Given the n selectors_q QuantumRegister, initialize w qubits to 1. w is the weight of the error.

    :param circuit: the quantum circuit
    :param selectors_q: the QuantumRegister representing the n columns selectors
    :param w: the error weight
    :returns: None

    """
    _logger.debug(
        "n_choose_w -> initializing {0} selectors qubits to 1".format(w))
    # Initialize 2 bits to 1, all the others to 0
    for i in range(w):
        circuit.x(selectors_q[i])


def permutation(circuit, selectors_q, flip_q):
    n = len(selectors_q)
    _logger.debug("Permutation -> input n is {0}".format(n))
    if (flip_q is None):
        flips_counter = int(log(n, 2)) * int(n / 2)
        _logger.debug("Permutation -> Number of hadamard qubits is {0}".format(
            flips_counter))
        flip_q = QuantumRegister(flips_counter, "flip")
        circuit.add_register(flip_q)
    ancilla_used = 0

    # Hadamard all ancillas
    circuit.h(flip_q)
    circuit.barrier()
    permutation_support(circuit, selectors_q, flip_q, ancilla_used, 0, n,
                        int(n / 2))
    circuit.barrier()
    return flip_q


def permutation_support(circuit, selectors_q, flip_q, ancilla_used, start, end,
                        swap_step):
    _logger.debug(
        "Permutation support -> Start: {0}, end: {1}, swap_step: {2}".format(
            start, end, swap_step))
    if (swap_step == 0 or start >= end):
        _logger.debug("Permutation support -> Base case recursion")
        return ancilla_used
    for i in range(start, int((start + end) / 2)):
        _logger.debug(
            "Permutation support -> Cswapping {0} & {1} using hadamard {2}".
            format(i, i + swap_step, ancilla_used))
        circuit.cswap(flip_q[ancilla_used], selectors_q[i],
                      selectors_q[i + swap_step])
        ancilla_used += 1
    _logger.debug("Permutation support -> Ancilla used after FOR {0}".format(
        ancilla_used))
    ancilla_used = permutation_support(circuit, selectors_q, flip_q,
                                       ancilla_used, start,
                                       int((start + end) / 2),
                                       int(swap_step / 2))
    _logger.debug(
        "Permutation support -> Ancilla used after FIRST recursion {0}".format(
            ancilla_used))
    ancilla_used = permutation_support(circuit, selectors_q,
                                       flip_q, ancilla_used,
                                       int((start + end) / 2), end,
                                       int(swap_step / 2))
    _logger.debug(
        "Permutation support -> Ancilla used after SECOND recursion {0}".
        format(ancilla_used))
    return ancilla_used


def permutation_i(circuit, selectors_q, flip_q):
    n = len(selectors_q)
    _logger.debug("Permutation_i -> input n is {0}".format(n))
    ancilla_counter = len(flip_q)
    _logger.debug("Permutation_i -> Number of hadamard qubits is {0}".format(
        ancilla_counter))

    permutation_support_i(circuit, selectors_q, flip_q, ancilla_counter - 1, 0,
                          n, int(n / 2))
    # Hadamard all ancillas
    circuit.h(flip_q)
    circuit.barrier()


def permutation_support_i(circuit, selectors_q, flip_q, ancilla_used, start,
                          end, swap_step):
    _logger.debug(
        "Permutation support_i -> Start: {0}, end: {1}, swap_step: {2}".format(
            start, end, swap_step))
    if (swap_step == 0 or start >= end):
        _logger.debug("Permutation support_i -> Base case recursion")
        return ancilla_used
    ancilla_used = permutation_support_i(circuit, selectors_q,
                                         flip_q, ancilla_used,
                                         int((start + end) / 2), end,
                                         int(swap_step / 2))
    _logger.debug(
        "Permutation support_i -> Ancilla used after FIRST recursion {0}".
        format(ancilla_used))
    ancilla_used = permutation_support_i(circuit, selectors_q, flip_q,
                                         ancilla_used, start,
                                         int((start + end) / 2),
                                         int(swap_step / 2))
    _logger.debug(
        "Permutation support_i -> Ancilla used after SECOND recursion {0}".
        format(ancilla_used))
    for i in range(int((start + end) / 2) - 1, start - 1, -1):
        _logger.debug(
            "Permutation support_i -> Cswapping {0} & {1} using hadamard {2}".
            format(i, i + swap_step, ancilla_used))
        circuit.cswap(flip_q[ancilla_used], selectors_q[i],
                      selectors_q[i + swap_step])
        ancilla_used -= 1
    _logger.debug("Permutation support_i -> Ancilla used after FOR {0}".format(
        ancilla_used))
    return ancilla_used


def matrix2gates(qc, h, selectors_q, sum_q):
    _logger.debug("matrix2gates -> initializing")
    r = h.shape[0]  # 3, rows
    n = h.shape[1]  # 8, columns
    if (sum_q is None):
        sum_q = QuantumRegister(r, 'sum')
        qc.add_register(sum_q)
    for i in range(n):
        for j in range(r):
            if h[j][i] == 1:
                _logger.debug("1 at [{0},{1}]".format(j, i))
                qc.cx(selectors_q[i], sum_q[j])
        qc.barrier()

    return sum_q


def matrix2gates_i(qc, h, selectors_q, sum_q):
    _logger.debug("matrix2gates_i -> initializing")
    r = h.shape[0]  # 3, rows
    n = h.shape[1]  # 8, columns
    for i in range(n - 1, -1, -1):
        for j in range(r - 1, -1, -1):
            if h[j][i] == 1:
                _logger.debug("1 at [{1}, {0}]".format(i, j))
                qc.cx(selectors_q[i], sum_q[j])
        qc.barrier()


def syndrome2gates(qc, sum_q, s):
    _logger.debug("syndrome2gates -> initializing")
    for i in range(len(s)):
        if (s[i] == 0):
            _logger.debug("0 at [{0}]".format(i))
            qc.x(sum_q[i])
    qc.barrier()


def oracle(qc, sum_q, pseudo_target, anc):
    _logger.debug("oracle -> initializing")
    single_control = composed_gates.n_control_compute(qc, sum_q, anc)
    # copy
    m = len(pseudo_target)
    for i in range(m):
        qc.cz(single_control, pseudo_target[i])
    composed_gates.n_control_uncompute(qc, sum_q, anc)
    return single_control


def negate_for_inversion(qc, *registers):
    for register in registers:
        qc.x(register)


# single control sum is not a QuantumRegister, but a qubit
def inversion_about_zero(qc, pseudo_control_register, inversion_qubit,
                         ancillas_inversion):
    _logger.debug("inversion_about_zero -> initializing")
    qc.barrier()

    single_control_inversion = composed_gates.n_control_compute(
        qc, pseudo_control_register, ancillas_inversion)

    qc.cz(single_control_inversion, inversion_qubit)

    composed_gates.n_control_uncompute(qc, pseudo_control_register,
                                       ancillas_inversion)

    qc.barrier()
    return single_control_inversion, ancillas_inversion


# param is a dictionary containing n, r, partial_drawing and img_dir
def build_circuit(h, syndrome, w, partial_drawing=False, img_dir=None):
    n = h.shape[1]
    r = h.shape[0]
    _logger.debug("n: {0}, r: {1}, partial_drawing: {2}, img_dir: {3}".format(
        n, r, partial_drawing, img_dir))

    qc, selectors_q = initialize_circuit(n)
    n_choose_w(qc, selectors_q, w)
    if partial_drawing:
        circuit_drawer(
            qc, filename='img/grovering_nchoosew.png', output='latex')

    flip_q = permutation(qc, selectors_q, None)
    if partial_drawing:
        circuit_drawer(
            qc, filename='img/grovering_permutation.png', output='latex')
    sum_q = matrix2gates(qc, h, selectors_q, None)
    syndrome2gates(qc, sum_q, syndrome)
    if partial_drawing:
        circuit_drawer(
            qc, filename='img/grovering_matrix_syndrome.png', output='latex')

    pseudo_ancilla_register = pse.PseudoQuantumRegister()
    pseudo_target_oracle = pse.PseudoQuantumRegister('oracle_targets')
    pseudo_control_inversion = pse.PseudoQuantumRegister('inversion_controls')

    # First grover, to initialize everything
    pseudo_target_oracle.add_registers(selectors_q, flip_q)
    single_control_sum = oracle(qc, sum_q, pseudo_target_oracle,
                                pseudo_ancilla_register)
    if partial_drawing:
        circuit_drawer(qc, filename='img/grovering_oracle.png', output='latex')

    syndrome2gates(qc, sum_q, syndrome)
    matrix2gates_i(qc, h, selectors_q, sum_q)
    if partial_drawing:
        circuit_drawer(
            qc, filename='img/grovering_matrix_syndrome_i.png', output='latex')
    permutation_i(qc, selectors_q, flip_q)
    n_choose_w(qc, selectors_q, w)
    if partial_drawing:
        circuit_drawer(
            qc, filename='img/grovering_permutation_i.png', output='latex')

    pseudo_control_inversion.add_registers(selectors_q, flip_q)
    pseudo_control_inversion.add_qubits(single_control_sum)

    negate_for_inversion(qc, selectors_q, flip_q)
    single_control_inversion = inversion_about_zero(
        qc, pseudo_control_inversion, selectors_q[0], pseudo_ancilla_register)
    negate_for_inversion(qc, selectors_q, flip_q)
    if partial_drawing:
        circuit_drawer(
            qc, filename='img/grovering_inversion.png', output='latex')

    n_choose_w(qc, selectors_q, w)
    permutation(qc, selectors_q, flip_q)

    # Remaining grover iterations
    rounds = int(round((pi / 2 * sqrt(n) - 1) / 2))
    _logger.debug("{0} rounds required".format(rounds - 1))
    for i in range(rounds - 1):
        _logger.debug("ITERATION {0}".format(i))
        matrix2gates(qc, h, selectors_q, sum_q)
        syndrome2gates(qc, sum_q, syndrome)

        oracle(qc, sum_q, pseudo_target_oracle, pseudo_ancilla_register)
        syndrome2gates(qc, sum_q, syndrome)
        matrix2gates_i(qc, h, selectors_q, sum_q)
        permutation_i(qc, selectors_q, flip_q)
        n_choose_w(qc, selectors_q, w)

        negate_for_inversion(qc, selectors_q, flip_q)
        inversion_about_zero(qc, pseudo_control_inversion, selectors_q[0],
                             pseudo_ancilla_register)
        negate_for_inversion(qc, selectors_q, flip_q)

        n_choose_w(qc, selectors_q, w)
        permutation(qc, selectors_q, flip_q)

    return qc, selectors_q
