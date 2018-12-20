from math import log, sqrt, pi
import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
import logging


def initialize_circuit(n, w):
    computing_q = QuantumRegister(n, 'q-com')
    circuit = QuantumCircuit(computing_q)

    # Initialize r bits to 1, all the others to 0
    for i in range(w):
        circuit.x(computing_q[i])

    return circuit, computing_q


# n is the original set of registers
# A.T.M. works only w/ n = to a power of 2
def permutation_old(circuit, computing_q):
    n = len(computing_q)
    _logger.debug("Permutation input n is {0}".format(n))
    ancilla_counter = int(log(n, 2)) * int(n / 2)
    ancilla_flip_q = QuantumRegister(ancilla_counter)
    circuit.add(ancilla_flip_q)

    # Hadamard all ancillas
    circuit.h(ancilla_flip_q)
    circuit.barrier()

    for i in range(0, n - int(n / 2), 1):
        ancilla_counter -= 1
        print("cswapping {0} {1}".format(i, i + n / 2))
        circuit.cswap(ancilla_flip_q[ancilla_counter], computing_q[i],
                      computing_q[i + int(n / 2)])
    print("*******")
    circuit.barrier()

    for i in range(0, n - int(n / 4), int(n / 2)):
        ancilla_counter -= 1
        print("cswapping {0} {1}".format(i, i + n / 4))
        circuit.cswap(ancilla_flip_q[ancilla_counter], computing_q[i],
                      computing_q[i + int(n / 4)])
        ancilla_counter -= 1
        print("cswapping {0} {1}".format(i + 1, i + 1 + int(n / 4)))
        circuit.cswap(ancilla_flip_q[ancilla_counter], computing_q[i + 1],
                      computing_q[i + 1 + int(n / 4)])
    print("*******")
    circuit.barrier()

    for i in range(0, n - int(n / 8), int(n / 4)):
        ancilla_counter -= 1
        print("cswapping {0} {1}".format(i, i + 1))
        circuit.cswap(ancilla_flip_q[ancilla_counter], computing_q[i],
                      computing_q[i + 1])
    print("*******")
    circuit.barrier()
    return ancilla_flip_q


def permutation(circuit, computing_q):
    n = len(computing_q)
    _logger.debug("Permutation input n is {0}".format(n))
    ancilla_counter = int(log(n, 2)) * int(n / 2)
    _logger.debug("Number of hadamard qubits is {0}".format(ancilla_counter))
    ancilla_flip_q = QuantumRegister(ancilla_counter)
    circuit.add(ancilla_flip_q)
    ancilla_used = 0

    # Hadamard all ancillas
    circuit.h(ancilla_flip_q)
    circuit.barrier()
    permutation_support(circuit, computing_q, ancilla_flip_q, ancilla_used, 0,
                        n, int(n / 2))


def permutation_support(circuit, computing_q, ancilla_flip_q, ancilla_used,
                        start, end, swap_step):
    _logger.debug("Start: {0}, end: {1}, swap_step: {2}".format(
        start, end, swap_step))
    if (swap_step == 0 or start >= end):
        _logger.debug("Base case recursion")
        return ancilla_used
    for i in range(start, int((start + end) / 2)):
        _logger.debug("Cswapping {0} w/ {1}".format(i, i + swap_step))
        circuit.cswap(ancilla_flip_q[ancilla_used], computing_q[i],
                      computing_q[i + swap_step])
        ancilla_used += 1
    _logger.debug("Ancilla used after FOR {0}".format(ancilla_used))
    ancilla_used = permutation_support(circuit, computing_q, ancilla_flip_q,
                                       ancilla_used, start,
                                       int((start + end) / 2),
                                       int(swap_step / 2))
    _logger.debug(
        "Ancilla used after FIRST recursion {0}".format(ancilla_used))
    ancilla_used = permutation_support(circuit, computing_q,
                                       ancilla_flip_q, ancilla_used,
                                       int((start + end) / 2), end,
                                       int(swap_step / 2))
    _logger.debug(
        "Ancilla used after SECOND recursion {0}".format(ancilla_used))
    return ancilla_used


# WIP
def permutation_undo():
    for i in range(0, n - last4, last2):
        print("cswapping {0} {1}".format(i, i + last4))
        circuit.cswap(ancilla_flip_q[0], computing_q[i],
                      computing_q[i + last4])
        circuit.measure(ancilla_flip_q, ancilla_flip_c)
        circuit.h(ancilla_flip_q)
        print("cswapping {0} {1}".format(i + 1, i + 1 + last4))
        circuit.cswap(ancilla_flip_q[0], computing_q[i + 1],
                      computing_q[i + 1 + last4])
        circuit.measure(ancilla_flip_q, ancilla_flip_c)
        circuit.h(ancilla_flip_q)
    print("*******")
    circuit.barrier()

    for i in range(n - last2):
        print("cswapping {0} {1}".format(i, i + last2))
        circuit.cswap(ancilla_flip_q[0], computing_q[i],
                      computing_q[i + last2])
        circuit.measure(ancilla_flip_q, ancilla_flip_c)
        circuit.h(ancilla_flip_q)
    print("*******")
    circuit.barrier()


def matrix2gates(qc, h, selectors_q):
    r = h.shape[0]  # 3, rows
    n = h.shape[1]  # 8, columns
    sum_q = QuantumRegister(r)
    qc.add(sum_q)
    for i in range(n):
        for j in range(r):
            if h[j][i] == 1:
                qc.cx(selectors_q[i], sum_q[j])
        qc.barrier()

    return sum_q


def syndrome2gates(qc, sum_q, s):
    for i in range(len(s)):
        if (s[i] == 0):
            qc.x(sum_q[i])


def oracle(qc, sum_q, selectors_q):
    # TODO generalize w/ multi-control
    ancilla_support = QuantumRegister(2)
    qc.add(ancilla_support)
    qc.ccx(sum_q[0], sum_q[1], ancilla_support[0])
    qc.ccx(sum_q[1], sum_q[2], ancilla_support[1])
    for i in range(len(selectors_q)):
        qc.cz(ancilla_support[1], selectors_q[i])
    qc.barrier()
    # reset ancillas
    qc.ccx(sum_q[1], sum_q[2], ancilla_support[1])
    qc.ccx(sum_q[0], sum_q[1], ancilla_support[0])
    return ancilla_support


# ORACLE: 1) MATRIX + s; 2) FLIP ON ancillas set to 1
# DIFFUSION: 1) MATRIX_i 2) COMB_i 3) DIFFUSION
# REPEAT AGAIN COMB + MATRIX


def main():
    h8 = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 0],
                   [0, 1, 0], [0, 0, 1], [1, 0, 1]]).T
    syndromes7 = np.array([[0, 0, 1], [0, 1, 0], [0, 1, 1], [1, 0, 0],
                           [1, 0, 1], [1, 1, 0], [1, 1, 1]])
    h4 = np.array([[1, 1, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1]]).T
    syndromes4 = np.array([[0, 1, 0], [1, 1, 1], [1, 0, 0], [0, 0, 1]]).T
    error_patterns = np.array([[0, 0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 1, 0],
                               [0, 0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0],
                               [0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0],
                               [1, 0, 0, 0, 0, 0, 0]])

    h = h4
    syndromes = syndromes4

    w = 1
    r = h.shape[0]
    n = h.shape[1]
    k = n - r
    _logger.debug("W = {0}; n = {1}; r = {2}".format(w, n, r))

    qc, selectors_q = initialize_circuit(n, w)
    ancilla_flip_q = permutation(qc, selectors_q)
    sum_q = matrix2gates(qc, h, selectors_q)
    syndrome = syndromes[np.random.randint(syndromes4.shape[0])]
    print("Syndrome is {0}".format(syndrome))
    syndrome2gates(qc, sum_q, syndrome)
    ancilla_support = oracle(qc, sum_q, selectors_q)

    from os import sys
    # 1 online simulator, 0 local simulator, 2
    backend = int(sys.argv[1])
    # 1 draw, 0 not draw
    draw = int(sys.argv[2])

    if (draw == 1):
        print("Drawing")
        from qiskit.tools.visualization import circuit_drawer
        circuit_drawer(qc, filename='img/grovering.png')

    if (backend == 0):
        from qiskit import Aer
        backend = Aer.get_backend('qasm_simulator')
    elif (backend == 1):
        from qiskit import IBMQ
        IBMQ.load_accounts()
        backend = IBMQ.get_backend('ibmq_qasm_simulator')
    elif (backend == 2):
        pass

    print("Preparing execution")
    from qiskit import execute
    print("Execute")
    job = execute(qc, backend, shots=4098)
    print(job.job_id())
    result = job.result()
    print("Results ready")
    counts = result.get_counts(qc)
    print(counts)
    print(len(counts))

    from qiskit.tools.visualization import plot_histogram
    plot_histogram(counts)


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
