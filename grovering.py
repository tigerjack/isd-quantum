import logging
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


def usage():
    import argparse
    parser = argparse.ArgumentParser(description="Prange isd algorithm")
    parser.add_argument(
        'n', metavar='n', type=int, help='the n of the parity matrix H.')
    parser.add_argument(
        'r',
        metavar='r',
        type=int,
        help='the r (= n - k) of the parity matrix H.')
    parser.add_argument(
        '-r',
        '--real',
        action='store_true',
        help='Invoke the real device (implies -o). Default is simulator.')
    parser.add_argument(
        '-o',
        '--online',
        action='store_true',
        help=
        'Use the online IBMQ devices. Default is local (simulator). This option is automatically set when we want to use a real device (see -r).'
    )
    parser.add_argument(
        '-b',
        '--backend_name',
        help=
        "The name of the backend. At the moment, the available local backends are: qasm_simulator, statevector_simulator and unitary_simulator."
    )
    parser.add_argument(
        '-pd',
        '--partial_drawing',
        action='store_true',
        help='Draw the incremental images of the circuit')
    parser.add_argument(
        '-td',
        '--total_drawing',
        action='store_true',
        help='Draw the final image of the circuit')
    parser.add_argument(
        '--img_dir',
        help=
        'If you want to store the image of the circuit, you need to specify the directory.'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Plot the histogram of the results. Default is false')
    parser.add_argument(
        '--export_qasm_file',
        help='Export the circuit as qasm text in the specified file')
    args = parser.parse_args()
    return args


def get_sample_matrix_and_random_syndrome(n, r):
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
    if (n == 8 and r == 3):
        h = h8
        s = syndromes7
    elif (n == 4 and r == 3):
        h = h4
        s = syndromes4
    else:
        return None, None
    return h, s


def build_circuit(args):
    n = args.n
    r = args.r
    partial_drawing = args.partial_drawing
    img_dir = args.img_dir
    _logger.debug("n: {0}, r: {1}, partial_drawing: {2}, img_dir: {3}".format(
        n, r, partial_drawing, img_dir))

    global h, syndrome
    h, syndromes = get_sample_matrix_and_random_syndrome(n, r)
    w = 1
    _logger.debug("W = {0}; n = {1}; r = {2}".format(w, n, r))
    # Launch the circuit w/ a random syndrome
    syndrome = syndromes[np.random.randint(syndromes.shape[0])]
    _logger.debug("Syndrome is {0}".format(syndrome))

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


def run(qc, selectors_q, args):
    real = args.real
    online = True if real else args.online
    total_drawing = args.total_drawing
    img_dir = args.img_dir
    plot = args.plot
    backend_name = args.backend_name
    need_measures = True
    _logger.debug(
        "real: {0}, online: {1}, total_drawing: {2}, img_dir: {3}, plot: {4}, backend_name: {5}"
        .format(real, online, total_drawing, img_dir, plot, backend_name))
    if (backend_name not in ('statevector_simulator', 'unitary_simulator')):
        _logger.debug("Adding measures")
        n = args.n
        from qiskit import ClassicalRegister
        cr = ClassicalRegister(n, 'cols')
        qc.add_register(cr)
        qc.measure(selectors_q, cr)
    if (online):
        if (backend_name is None):
            backend_name = 'ibmq_qasm_simulator'
        from qiskit import IBMQ
        IBMQ.load_accounts()
        backend = IBMQ.get_backend(backend_name)
    else:
        if (backend_name is None):
            backend_name = 'qasm_simulator'
        from qiskit import Aer
        backend = Aer.get_backend(backend_name)

    _logger.debug("Preparing execution")
    from qiskit import execute
    _logger.debug("Execute")
    job = execute(qc, backend, shots=4098)
    _logger.debug(job.job_id())
    result = job.result()
    _logger.debug("Results ready")
    _logger.debug("Syndrome was {0}; H was \n{1}".format(syndrome, h))

    if backend_name in 'statevector_simulator':
        statevector = result.get_statevector(qc)
        _logger.debug("State vector is\n{0}".format(statevector))
        if plot:
            _logger.debug("Plotting")
            from qiskit.tools.visualization import plot_state_city
            plot_state_city(statevector)
    elif backend_name in 'unitary_simulator':
        unitary = result.get_unitary(qc)
        _logger.debug("Circuit unitary is:\n{0}".format(unitary))
    else:  # For qasm and real devices
        counts = result.get_counts(qc)
        _logger.debug("{0} results: \n {1}".format(len(counts), counts))
        if plot:
            _logger.debug("Plotting")
            from qiskit.tools.visualization import plot_histogram
            plot_histogram(counts)


def import_fat_modules():
    global log, sqrt, pi, np, QuantumCircuit, QuantumRegister, composed_gates, pse
    from math import log, sqrt, pi
    import numpy as np
    from qiskit import QuantumCircuit, QuantumRegister
    import composed_gates
    import pseudoquantumregister as pse


def main():
    args = usage()
    import_fat_modules()
    qc, selectors_q = build_circuit(args)
    s = args.export_qasm_file
    if s is not None:
        q = qc.qasm()
        _logger.debug("Exporing circuit")
        with open(s, "w+") as f:
            f.write(q)
        print(q)
        return
    run(qc, selectors_q, args)


if __name__ == "__main__":
    main()
