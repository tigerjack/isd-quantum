def usage():
    import argparse
    parser = argparse.ArgumentParser(description="Prange isd algorithm")
    parser.add_argument(
        'n', metavar='n', type=int, help='The n of the parity matrix H.')
    parser.add_argument(
        'r',
        metavar='r',
        type=int,
        help='The r (== n - k) of the parity matrix H.')
    parser.add_argument(
        'w', metavar='w', type=int, help='The weight of the error.')
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
        'Use the online IBMQ devices. Default is local (simulator). This option is automatically set to true when we want to use a real device (see -r).'
    )
    parser.add_argument(
        '-p',
        '--provider',
        default='basicaer',
        choices=['basicaer', 'aer', 'qcgpu', 'projectq', 'jku'],
        help=
        "The name of the provider. At the moment, the available local providers are: BasicAer, Aer, QCGPU, ProjectQ, JKU. On the other hand, IBMQ provider is only selected through the -o flag becuase it has different names for backends."
    )
    parser.add_argument(
        '-b',
        '--backend_name',
        default='qasm_simulator',
        choices=[
            'qasm_simulator', 'statevector_simulator', 'unitary_simulator'
        ],
        help=
        "The name of the backend. At the moment, the available local backends are: qasm_simulator (default), statevector_simulator and unitary_simulator."
    )
    parser.add_argument(
        '-i',
        '--infos',
        action='store_true',
        help=
        'Print only infos on the circuit built for the specific backend (such as the number of gates) without executing it.'
    )
    parser.add_argument(
        '-nx',
        '--not_execute',
        action='store_true',
        help='Do not execute the circuit.')
    parser.add_argument(
        '--img_dir',
        help=
        'If you want to store the image of the circuit, you need to specify the directory.'
    )
    parser.add_argument(
        '--draw_circuit',
        action='store_true',
        help='Draw the image of the circuit.')
    parser.add_argument(
        '--draw_dag',
        action='store_true',
        help='Draw the direct acyclic graph of the circuit.')
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
    _logger.debug(
        "Preparing execution with backend {0} from provider {1}".format(
            backend, backend.provider()))
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
    args.online = True if args.real else args.online
    _logger.debug("real: {0}, online: {1}, backend_name: {2}".format(
        args.real, args.online, args.backend_name))
    if (args.online):
        if (args.backend_name is None):
            if not args.real:
                args.backend_name = 'ibmq_qasm_simulator'
            else:
                # from qiskit.providers.ibmq import least_busy
                #     try:
                #         large_enough_devices = IBMQ.backends(
                #             filters=
                #             lambda x: x.configuration()['n_qubits'] >= n and x.configuration()['simulator'] == (not real)
                # )
                #         backend = least_busy(large_enough_devices)
                #         least_busy_device = least_busy(IBMQ.backends(simulator=False))
                raise "Real default device not yet implemented"
        from qiskit import IBMQ
        IBMQ.load_accounts()
        provider = IBMQ
    else:
        if (args.backend_name is None):
            args.backend_name = 'qasm_simulator'

        args.provider = args.provider.lower()

        if args.provider == "basicaer":
            from qiskit import BasicAer
            provider = BasicAer
        elif args.provider == "aer":
            from qiskit import Aer
            provider = Aer
        elif args.provider in ("projectqp", "projectqpprovider"):
            from qiskit_addon_projectq import ProjectQProvider
            provider = ProjectQProvider()
        elif args.provider in ("qcgpu", "qcgpuprovider"):
            from qiskit_qcgpu_provider import QCGPUProvider
            provider = QCGPUProvider()
        elif args.provider in ("jku", "jkuprovider"):
            from qiskit_addon_jku import JKUProvider
            provider = JKUProvider()
        else:
            raise "Invalid provider {0}".format(args.provider)
    backend = provider.get_backend(args.backend_name)
    return backend


def draw_circuit(qc, args):
    _logger.debug("Drawing circuit")
    img_file = args.img_dir + "prange_isd_{0}_{1}_{2}".format(
        args.n, args.r, args.w)
    style_mpl = {
        'cregbundle': True,
        'compress': True,
        'usepiformat': True,
        'subfontsize': 12,
        'fold': 100,
        'showindex': True,
        "displaycolor": {
            "id": "#ffca64",
            "u0": "#f69458",
            "u1": "#f69458",
            "u2": "#f69458",
            "u3": "#f69458",
            "x": "#a6ce38",
            "y": "#a6ce38",
            "z": "#a6ce38",
            "h": "#00bff2",
            "s": "#00bff2",
            "sdg": "#00bff2",
            "t": "#ff6666",
            "tdg": "#ff6666",
            "rx": "#ffca64",
            "ry": "#ffca64",
            "rz": "#ffca64",
            "reset": "#d7ddda",
            "target": "#00bff2",
            "meas": "#f070aa"
        }
    }
    from qiskit.tools.visualization import circuit_drawer
    circuit_drawer(qc, filename=img_file, style=style_mpl, output='mpl')
    # circuit_drawer(qc, filename=img_file, output='latex')
    # circuit_drawer(qc, filename=img_file, output='latex_source')
    # circuit_drawer(qc, filename=img_file, line_length=-1, output='text')


def draw_dag(qc, args):
    _logger.debug("Drawing DAG")
    from qiskit.converters import circuit_to_dag
    dag = circuit_to_dag(qc)
    img_file = args.img_dir + "prange_isd_{0}_{1}_{2}_dag".format(
        args.n, args.r, args.w)
    from qiskit.tools.visualization.dag_visualization import dag_drawer
    dag_drawer(dag, img_file)


def get_compiled_circuit_infos(qc, backend):
    result = {}
    _logger.debug("Getting infos ... ")
    # backend_coupling = backend.configuration()['coupling_map']
    result['n_qubits_qasm'] = qc.width()
    result['depth_qasm'] = qc.depth()
    result['count_ops'] = qc.count_ops()
    # result['n_gates_qasm'] = sum(qc.count_ops().values())
    result['n_gates_qasm'] = qc.size()
    result['num_tensor_factors'] = qc.num_tensor_factors()
    # qc_qasm = qc.qasm()
    # result['n_gates_qasm'] = len(qc_qasm.split("\n")) - 4
    # from qiskit import compile
    # qc_compiled = compile(qc, backend=backend)
    # qc_compiled_qasm = qc_compiled.experiments[0].header.compiled_circuit_qasm
    # result['n_gates_compiled'] = len(qc_compiled_qasm.split("\n")) - 4
    return result


def main():
    args = usage()
    load_modules()
    _logger.debug(args)
    n = args.n
    r = args.r
    w = args.w
    _logger.debug("w = {0}; n = {1}; r = {2}".format(w, n, r))

    backend = get_backend(args)
    _logger.debug("After function, backend name is {0}".format(backend.name()))

    h, syndrome = get_sample_matrix_and_random_syndrome(n, r)
    _logger.debug("Syndrome is {0}".format(syndrome))

    if (backend.name() in ('statevector_simulator', 'unitary_simulator')):
        _logger.debug("Measures not needed")
        need_measures = False
    else:
        _logger.debug("Measures needed")
        need_measures = True
    qc, selectors_q = prange_isd.build_circuit(h, syndrome, w, need_measures)

    s = args.export_qasm_file
    if s is not None:
        q = qc.qasm()
        _logger.debug("Exporing circuit")
        with open(s, "w+") as f:
            f.write(q)

    if (args.infos):
        res = get_compiled_circuit_infos(qc, backend)
        for k, v in res.items():
            print("{0} --> {1}".format(k, v))

    if args.img_dir is None:
        args.img_dir = 'data/img/'
    if args.draw_circuit:
        draw_circuit(qc, args)
    if args.draw_dag:
        draw_dag(qc, args)

    if (args.not_execute):
        _logger.debug("Not execute set to true, exiting.")
        return

    result = run(qc, backend)

    plot = args.plot
    if backend.name() in 'statevector_simulator':
        statevector = result.get_statevector(qc)
        _logger.debug("State vector is\n{0}".format(statevector))
        if plot:
            _logger.debug("Plotting")
            from qiskit.tools.visualization import plot_state_city
            plot_state_city(statevector)
    elif backend.name() in 'unitary_simulator':
        unitary = result.get_unitary(qc)
        _logger.debug("Circuit unitary is:\n{0}".format(unitary))
    else:  # For qasm and real devices
        counts = result.get_counts(qc)
        _logger.debug("{0} results: \n {1}".format(len(counts), counts))
        if plot:
            _logger.debug("Plotting")
            from qiskit.tools.visualization import plot_histogram
            plot_histogram(counts)
    _logger.debug("H was\n{0}\nSyndrome was\n{1}".format(h, syndrome))


if __name__ == "__main__":
    main()
