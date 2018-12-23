from math import log, sqrt, pi
import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
import logging
import composed_gates
import pseudoquantumregister as pse


def initialize_circuit(n):
    _logger.debug(
        "initialize_circuit -> creating n = {0} qubits for selection".format(
            n))
    selectors_q = QuantumRegister(n, 'select')
    circuit = QuantumCircuit(selectors_q)

    return circuit, selectors_q


def n_choose_w(circuit, selectors_q, w):
    _logger.debug("n_choose_w -> initializing {0} qubits to 1".format(w))
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
                qc.cx(selectors_q[i], sum_q[j])
        qc.barrier()


def syndrome2gates(qc, sum_q, s):
    _logger.debug("syndrome2gates -> initializing")
    for i in range(len(s)):
        if (s[i] == 0):
            qc.x(sum_q[i])
    qc.barrier()


def oracle(qc, sum_q, pseudo_target, anc):
    _logger.debug("oracle -> initializing")
    single_control = composed_gates.n_control_compute(qc, sum_q, anc)
    # copy
    m = len(pseudo_target)
    for i in range(m):
        qc.cz(single_control, pseudo_target[i])
    return single_control


# single control sum is not a QuantumRegister, but a qubit
def inversion_about_zero(qc, pseudo_control_register, inversion_qubit,
                         ancillas_inversion):
    _logger.debug("inversion_about_zero -> initializing")
    qc.barrier()
    for qubit in pseudo_control_register:
        qc.x(qubit)
    qc.barrier()

    single_control_inversion = composed_gates.n_control_compute(
        qc, pseudo_control_register, ancillas_inversion)

    qc.cz(single_control_inversion, inversion_qubit)

    composed_gates.n_control_uncompute(qc, pseudo_control_register,
                                       ancillas_inversion)

    qc.barrier()
    for qubit in pseudo_control_register:
        qc.x(qubit)
    qc.barrier()
    return single_control_inversion, ancillas_inversion


# n is the original set of registers
# A.T.M. works only w/ n = to a power of 2
def permutation_old(circuit, selectors_q, flip_q):
    n = len(selectors_q)
    _logger.debug("Permutation input n is {0}".format(n))
    ancilla_counter = int(log(n, 2)) * int(n / 2)
    if flip_q is None:
        flip_q = QuantumRegister(ancilla_counter)
        circuit.add(flip_q)

    # Hadamard all ancillas
    circuit.h(flip_q)
    circuit.barrier()

    for i in range(0, n - int(n / 2), 1):
        ancilla_counter -= 1
        print("cswapping {0} {1}".format(i, i + n / 2))
        circuit.cswap(flip_q[ancilla_counter], selectors_q[i],
                      selectors_q[i + int(n / 2)])
    print("*******")
    circuit.barrier()

    for i in range(0, n - int(n / 4), int(n / 2)):
        ancilla_counter -= 1
        print("cswapping {0} {1}".format(i, i + n / 4))
        circuit.cswap(flip_q[ancilla_counter], selectors_q[i],
                      selectors_q[i + int(n / 4)])
        ancilla_counter -= 1
        print("cswapping {0} {1}".format(i + 1, i + 1 + int(n / 4)))
        circuit.cswap(flip_q[ancilla_counter], selectors_q[i + 1],
                      selectors_q[i + 1 + int(n / 4)])
    print("*******")
    circuit.barrier()

    # for i in range(0, n - int(n / 8), int(n / 4)):
    #     ancilla_counter -= 1
    #     print("cswapping {0} {1}".format(i, i + 1))
    #     circuit.cswap(flip_q[ancilla_counter], selectors_q[i],
    #                   selectors_q[i + 1])
    print("*******")
    circuit.barrier()
    return flip_q


def permutation_old_i(circuit, selectors_q, flip_q):
    n = len(selectors_q)
    _logger.debug("Permutation input n is {0}".format(n))
    ancilla_counter = 0

    # for i in range(n - int(n / 8) - 1, -1, -int(n / 4)):
    #     print("cswapping {0} {1}".format(i, i + 1))
    #     circuit.cswap(flip_q[ancilla_counter], selectors_q[i],
    #                   selectors_q[i + 1])
    #     ancilla_counter += 1
    # print("*******")

    for i in range(n - int(n / 4) - 1, -1, -int(n / 2)):
        print("cswapping {0} {1}".format(i, i + n / 4))
        circuit.cswap(flip_q[ancilla_counter], selectors_q[i],
                      selectors_q[i + int(n / 4)])
        ancilla_counter += 1
        print("cswapping {0} {1}".format(i + 1, i + 1 + int(n / 4)))
        circuit.cswap(flip_q[ancilla_counter], selectors_q[i + 1],
                      selectors_q[i + 1 + int(n / 4)])
        ancilla_counter += 1

    for i in range(n - int(n / 2) - 1, -1, -1):
        print("cswapping {0} {1}".format(i, i + n / 2))
        circuit.cswap(flip_q[ancilla_counter], selectors_q[i],
                      selectors_q[i + int(n / 2)])
        ancilla_counter += 1
    print("*******")
    circuit.barrier()

    print("*******")
    circuit.barrier()

    circuit.barrier()
    circuit.h(flip_q)
    circuit.barrier()


def main():
    h8 = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 0],
                   [0, 1, 0], [0, 0, 1], [1, 0, 1]]).T
    syndromes7 = np.array([[0, 0, 1], [0, 1, 0], [0, 1, 1], [1, 0, 0],
                           [1, 0, 1], [1, 1, 0], [1, 1, 1]])
    error_patterns7 = np.array([[0, 0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 1, 0],
                                [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0],
                                [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0],
                                [1, 0, 0, 0, 0, 0, 0]])

    h4 = np.array([[1, 1, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1]]).T
    syndromes4 = np.array([[0, 1, 0], [1, 1, 1], [1, 0, 0], [0, 0, 1]])

    h = h8
    syndromes = syndromes7

    w = 1
    r = h.shape[0]
    n = h.shape[1]
    k = n - r
    _logger.debug("W = {0}; n = {1}; r = {2}".format(w, n, r))
    syndrome = syndromes[np.random.randint(syndromes.shape[0])]
    print("Syndrome is {0}".format(syndrome))

    qc, selectors_q = initialize_circuit(n)
    n_choose_w(qc, selectors_q, w)
    flip_q = permutation(qc, selectors_q, None)
    # flip_q = permutation_old(qc, selectors_q, None)
    sum_q = matrix2gates(qc, h, selectors_q, None)
    syndrome2gates(qc, sum_q, syndrome)

    pseudo_ancilla_register = pse.PseudoQuantumRegister()
    pseudo_target_oracle = pse.PseudoQuantumRegister('oracle_targets')
    pseudo_control_inversion = pse.PseudoQuantumRegister('inversion_controls')

    # First grover, to initialize everything
    pseudo_target_oracle.add_registers(selectors_q, flip_q)
    single_control_sum = oracle(qc, sum_q, pseudo_target_oracle,
                                pseudo_ancilla_register)

    syndrome2gates(qc, sum_q, syndrome)
    matrix2gates_i(qc, h, selectors_q, sum_q)
    permutation_i(qc, selectors_q, flip_q)
    # permutation_old_i(qc, selectors_q, flip_q)
    n_choose_w(qc, selectors_q, w)

    pseudo_control_inversion.add_registers(selectors_q, flip_q)
    pseudo_control_inversion.add_qubits(single_control_sum)

    single_control_inversion = inversion_about_zero(
        qc, pseudo_control_inversion, selectors_q[0], pseudo_ancilla_register)

    n_choose_w(qc, selectors_q, w)
    permutation(qc, selectors_q, flip_q)
    # Stop here for the real result
    matrix2gates(qc, h, selectors_q, sum_q)
    syndrome2gates(qc, sum_q, syndrome)

    for i in range(0):
        _logger.debug("ITERATION {0}".format(i))
        oracle(qc, sum_q, pseudo_target_oracle, pseudo_ancilla_register)
        syndrome2gates(qc, sum_q, syndrome)
        matrix2gates_i(qc, h, selectors_q, sum_q)
        permutation_i(qc, selectors_q, flip_q)
        n_choose_w(qc, selectors_q, w)

        inversion_about_zero(qc, pseudo_control_inversion, selectors_q[0],
                             pseudo_ancilla_register)

        n_choose_w(qc, selectors_q, w)
        permutation(qc, selectors_q, flip_q)
        matrix2gates(qc, h, selectors_q, sum_q)
        syndrome2gates(qc, sum_q, syndrome)

    from os import sys
    # 1 online simulator, 0 local simulator, 2
    backend_choice = int(sys.argv[1])
    # 1 draw, 0 not draw
    draw = int(sys.argv[2])

    # 2 should be statevector
    if (backend_choice == 0):
        print("Backend offline")
        cr = ClassicalRegister(n, 'cols')
        qc.add_register(cr)
        qc.measure(selectors_q, cr)
        from qiskit import Aer
        backend = Aer.get_backend('qasm_simulator')
    elif (backend_choice == 1):
        print("Backend online")
        cr = ClassicalRegister(n, 'cols')
        qc.add_register(cr)
        qc.measure(selectors_q, cr)
        from qiskit import IBMQ
        IBMQ.load_accounts()
        backend = IBMQ.get_backend('ibmq_qasm_simulator')
    elif (backend_choice == 2):
        print("Backend statevector")
        from qiskit import Aer
        backend = Aer.get_backend('statevector_simulator')

    if (draw == 1):
        print("Drawing")
        from qiskit.tools.visualization import circuit_drawer
        circuit_drawer(qc, filename='img/grovering.png')

    print("Preparing execution")
    from qiskit import execute
    print("Execute")
    job = execute(qc, backend, shots=4098)
    print(job.job_id())
    result = job.result()
    print("Results ready")
    if (backend_choice == 0 or backend_choice == 1):
        counts = result.get_counts(qc)
        print(counts)
        print(len(counts))
        to_plot = counts

    elif (backend_choice == 2):
        statevector = result.get_statevector(qc)
        print("State vector is {0}".format(statevector))
        to_plot = statevector

    _logger.debug("Syndrome was {0}; H was \n{1}".format(syndrome, h))

    from qiskit.tools.visualization import plot_histogram
    plot_histogram(to_plot)


_logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
_formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
_handler.setFormatter(_formatter)
if (_logger.hasHandlers()):
    _logger.handlers.clear()
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)
if __name__ == "__main__":
    main()
