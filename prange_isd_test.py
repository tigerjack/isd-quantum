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
    import numpy as np
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
        syndromes = syndromes7
    elif (n == 4 and r == 3):
        h = h4
        syndromes = syndromes4
    else:
        return None, None
    return h, syndromes[np.random.randint(syndromes.shape[0])]


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
        from qiskit import ClassicalRegister, QuantumCircuit
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


def load_modules():
    global logging, prange_isd, _logger
    import logging
    import prange_isd
    _logger = logging.getLogger(__name__)
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    _handler.setFormatter(_formatter)
    if (_logger.hasHandlers()):
        _logger.handlers.clear()
        _logger.addHandler(_handler)
    _logger.setLevel(logging.DEBUG)


def main():
    args = usage()
    load_modules()
    n = args.n
    r = args.r
    w = 1
    partial_drawing = args.partial_drawing
    img_dir = args.img_dir
    h, syndrome = get_sample_matrix_and_random_syndrome(n, r)
    _logger.debug("W = {0}; n = {1}; r = {2}".format(w, n, r))

    _logger.debug("Syndrome is {0}".format(syndrome))
    qc, selectors_q = prange_isd.build_circuit(h, syndrome, w, partial_drawing,
                                               img_dir)
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
