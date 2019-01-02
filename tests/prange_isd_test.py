def usage():
    import argparse
    parser = argparse.ArgumentParser(description="Prange isd algorithm")
    parser.add_argument(
        'n', metavar='n', type=int, help='the n of the parity matrix H.')
    parser.add_argument(
        'r',
        metavar='r',
        type=int,
        help='the r (== n - k) of the parity matrix H.')
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


def run(qc, backend):
    _logger.debug("Preparing execution")
    from qiskit import execute
    _logger.debug("Execute")
    job = execute(qc, backend, shots=4098)
    _logger.debug(job.job_id())
    result = job.result()
    _logger.debug("Results ready")
    return result


def load_modules():
    global logging, _logger
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
    import os
    import sys
    sys.path.insert(
        0, os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'src')))
    _logger.debug("Loading prange isd")
    global prange_isd
    import prange_isd


def get_backend(args):
    real = args.real
    online = True if real else args.online
    backend_name = args.backend_name
    _logger.debug("real: {0}, online: {1}, backend_name: {2}".format(
        real, online, backend_name))
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
    return backend, backend_name


def main():
    args = usage()
    load_modules()
    n = args.n
    r = args.r
    w = 1
    _logger.debug("w = {0}; n = {1}; r = {2}".format(w, n, r))

    backend_name = args.backend_name
    backend, backend_name = get_backend(args)
    _logger.debug("After function, backend name is {0}".format(backend_name))

    h, syndrome = get_sample_matrix_and_random_syndrome(n, r)
    _logger.debug("Syndrome is {0}".format(syndrome))

    if (backend_name in ('statevector_simulator', 'unitary_simulator')):
        _logger.debug("Measures not needed")
        need_measures = False
    else:
        _logger.debug("Measures needed")
        need_measures = True
    qc, selectors_q = prange_isd.build_circuit(h, syndrome, w, need_measures)

    img_dir = args.img_dir
    if img_dir is not None:
        _logger.debug("Drawing")
        img_file = img_dir + "prange_isd_{0}_{1}_{2}".format(n, r, w)
        from qiskit.tools.visualization import circuit_drawer
        circuit_drawer(
            qc,
            filename=img_file,
            style={
                'cregbundle': True,
                'compress': True,
                'fold': 40
            },
            output='mpl')
        # circuit_drawer(qc, filename=img_file, output='latex')
        # circuit_drawer(qc, filename=img_file, output='latex_source')
        # circuit_drawer(qc, filename=img_file, line_length=-1, output='text')

    s = args.export_qasm_file
    if s is not None:
        q = qc.qasm()
        _logger.debug("Exporing circuit")
        with open(s, "w+") as f:
            f.write(q)
        return
    result = run(qc, backend)

    plot = args.plot
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


if __name__ == "__main__":
    main()
