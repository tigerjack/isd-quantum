def usage():
    import argparse
    parser = argparse.ArgumentParser(
        description="Collection of isd algorithms for quantum computers")
    parser.add_argument(
        'n', metavar='n', type=int, help='The n of the parity matrix H.')
    parser.add_argument(
        'r',
        metavar='r',
        type=int,
        help='The r (== n - k) of the parity matrix H.')
    parser.add_argument(
        'd', metavar='d', type=int, help='The hamming distance.')
    parser.add_argument(
        'w', metavar='w', type=int, help='The weight of the error.')
    parser.add_argument(
        '-m',
        help='The isd choice',
        required=True,
        choices=['bruteforce', 'lee_brickell'],
    )
    parser.add_argument(
        '--mct_mode',
        choices=['basic', 'advanced', 'noancilla'],
        default='advanced',
        help=
        'Mode for the multi-controlled Toffoli gates. Basic uses a V shape simple CNOTs, but a huge number of ancillas. Advanced (default) uses just a single ancilla, while noancilla uses none. However, these last two modes, expecially noancilla, significantly increase the depth of the circuit and the number of gates.'
    )
    parser.add_argument(
        '--nwr_mode',
        choices=['benes', 'fpc'],
        default='benes',
        #TODO
        help='Mode for the nwr')
    parser.add_argument(
        '-r',
        '--real',
        action='store_true',
        help=
        'Invoke the real quantum device (implies -o). Default is a simulator.')
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
        # choices=['basicaer', 'aer', 'qcgpu', 'projectq', 'jku', 'ibmq'],
        help=
        "The name of the provider. At the moment, the available local providers are: BasicAer, Aer, QCGPU, ProjectQ, JKU, IBMQ. The default choices are IBMQ for online execution (see -o) and BasicAer for local execution."
    )
    parser.add_argument(
        '-b',
        '--backend_name',
        # choices=[
        #     'qasm_simulator', 'statevector_simulator', 'unitary_simulator'
        # ],
        help=
        "The name of the backend. At the moment, the available local backend simulators are: qasm_simulator (default), statevector_simulator and unitary_simulator. The available online backend simulator is ibmq_qasm_simulator (default if -r flag is not used). On the other hand, the real quantum device backend list may vary in time. If -r is active and you don't provide a default choice for backend_name, the least busy device large enough to run the circuit is selected."
    )
    parser.add_argument(
        '-i',
        '--infos',
        action='store_true',
        help=
        'Print infos on the circuit built for the specific backend (such as the number of gates). At the moment, it prints the infos only on stdout.'
    )
    parser.add_argument(
        '-nx',
        '--not_execute',
        action='store_true',
        help=
        'Do not execute the circuit. Useful for example when you just want infos (see -i) or a picture of the circuit (see --draw_circuit)'
    )
    parser.add_argument(
        '-d',
        '--draw_circuit',
        action='store_true',
        help='Draw the image of the circuit.')
    parser.add_argument(
        '--img_dir',
        help=
        'If you want to store the image of the circuit, you need to specify the directory.'
    )
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


def clean_args(args):
    # if user wants a real simulator, then we should go online
    args.online = True if args.real else args.online
    # if user didn't provide a backend name, we impose a default one
    # The default choice is the 'qasm_simulator' for a simulation,
    # a large enough device for a real execution
    if args.backend_name is None:
        if args.online:
            if args.real:
                # enough means get a large enough device to run the circuit
                args.backend_name = 'enough'
            else:
                args.backend_name = 'ibmq_qasm_simulator'
        else:
            args.backend_name = 'qasm_simulator'
    # Same for providers
    # Default choices are IBMQ for online execution, BasicAer for offline.
    if args.provider is None:
        if args.online:
            args.provider = 'ibmq'
        else:
            from qiskit import BasicAer
            args.provider = 'basicaer'
    if args.draw_circuit and args.img_dir is None:
        args.img_dir = 'data/img/'


def load_modules():
    global logging, logger
    import logging
    import os
    logging_level = logging._nameToLevel.get(os.getenv('LOG_LEVEL'), 'INFO')
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        # '%(asctime)s %(levelname)-8s %(name)-12s %(funcName)-12s %(message)s')
        '>%(levelname)-8s %(name)-12s %(funcName)-12s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging_level)
    global BruteforceISD, LeeBrickellISD
    from isdquantum.methods.bruteforce import BruteforceISD
    from isdquantum.methods.lee_brickell import LeeBrickellISD
    other_isd_loggers = logging.getLogger('isdquantum.methods')
    other_isd_loggers.setLevel(logging_level)
    other_isd_loggers.addHandler(handler)


def get_backend(args, n_qubits):
    logger.debug("real: {0}, online: {1}, backend_name: {2}".format(
        args.real, args.online, args.backend_name))
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
    elif args.provider in ("ibmq"):
        from qiskit import IBMQ
        IBMQ.load_accounts()
        provider = IBMQ
    else:
        raise Exception("Invalid provider {0}".format(args.provider))

    # only for real, online execution
    if args.backend_name == 'enough' and args.provider == 'ibmq':
        from qiskit.providers.ibmq import least_busy
        large_enough_devices = provider.backends(
            filters=lambda x: x.configuration(
            ).n_qubits >= n_qubits and x.configuration().simulator == False)
        backend = least_busy(large_enough_devices)
    else:
        backend = provider.get_backend(args.backend_name)
        if backend.configuration().n_qubits < n_qubits:
            raise Exception(
                "Backend {0} on provider {1} has only {2} qubits, while {3} are needed."
                .format(backend.name(), backend.provider(),
                        backend.configuration().n_qubits, n_qubits))
    return backend


def get_sample_matrix_and_random_syndrome(n, k, d, w):
    logger.info("Trying to get isd parameters for {0}, {1}, {2}, {3}".format(
        n, k, d, w))
    from isdclassic.utils import rectangular_codes_hardcoded as rch
    from numpy.random import randint
    h, _, syndromes, _, _, _ = rch.get_isd_systematic_parameters(n, k, d, w)
    return h, syndromes[randint(syndromes.shape[0])]


def run(qc, backend):
    logger.info(
        "Preparing execution with backend {0} from provider {1}".format(
            backend, backend.provider()))
    from qiskit import execute
    logger.debug("Execute")
    job = execute(qc, backend, shots=8192)
    logger.info("Job id is {0}".format(job.job_id()))
    if (not backend.status().operational or backend.status().pending_jobs > 2
            or backend.status().status_msg == 'calibrating'):
        logger.warn(
            "Backend {0} from provider {1} can't execute the circuit any time soon, try to retrieve the result using the job id later on"
            .format(backend, backend.provider()))
        return None
    result = job.result()
    logger.debug("Results ready")
    return result


def draw_circuit(qc, args):
    logger.info("Drawing circuit")
    img_file = args.img_dir + qc.name
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
    circuit_drawer(
        qc, filename=img_file + ".png", style=style_mpl, output='mpl')
    # print("Drawn")
    # circuit_drawer(qc, filename=img_file, output='latex')
    # circuit_drawer(qc, filename=img_file, output='latex_source')
    # circuit_drawer(qc, filename=img_file, line_length=-1, output='text')


def draw_dag(qc, args):
    logger.info("Drawing DAG")
    img_file = args.img_dir + qc.name
    from qiskit.converters import circuit_to_dag
    dag = circuit_to_dag(qc)
    from qiskit.tools.visualization.dag_visualization import dag_drawer
    dag_drawer(dag, img_file)


def get_compiled_circuit_infos(qc, backend):
    result = {}
    logger.debug("Getting infos ... ")
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


def drawing_at_end(qc, args):
    if args.draw_circuit:
        draw_circuit(qc, args)
    if args.draw_dag:
        draw_dag(qc, args)


def main():
    args = usage()
    clean_args(args)
    load_modules()
    n = args.n
    r = args.r
    d = args.d
    w = args.w
    logger.debug("w = {0}; n = {1}; r = {2}".format(w, n, r))

    h, syndrome = get_sample_matrix_and_random_syndrome(n, n - r, d, w)
    logger.debug("Syndrome is {0}".format(syndrome))

    if (args.backend_name in ('statevector_simulator', 'unitary_simulator')):
        logger.debug("Measures not needed")
        need_measures = False
    else:
        logger.debug("Measures needed")
        need_measures = True
    if args.m == 'bruteforce':
        isd_method = BruteforceISD(h, syndrome, w, need_measures,
                                   args.mct_mode, args.nwr_mode)
    elif args.m == 'lee_brickell':
        isd_method = LeeBrickellISD(h, syndrome, w, need_measures,
                                    args.mct_mode)
    print("Gonna build circuit with {0} {1}".format(args.mct_mode,
                                                    args.nwr_mode))
    qc = isd_method.build_circuit()

    s = args.export_qasm_file
    if s is not None:
        q = qc.qasm()
        logger.debug("Exporing circuit")
        with open(s, "w+") as f:
            f.write(q)

    n_qubits = qc.width()
    logger.info("Number of qubits needed = {0}".format(n_qubits))
    backend = get_backend(args, n_qubits)
    logger.debug("After function, backend name is {0}".format(backend.name()))

    if (args.infos):
        res = get_compiled_circuit_infos(qc, backend)
        for k, v in res.items():
            print("{0} --> {1}".format(k, v))

    if (args.not_execute):
        logger.debug("Not execute set to true, exiting.")
        drawing_at_end(qc, args)
        return

    result = run(qc, backend)
    if result is None:
        logger.info("Result is none")
        return
    plot = args.plot
    if backend.name() in 'statevector_simulator':
        statevector = result.get_statevector(qc)
        logger.info("State vector is\n{0}".format(statevector))
        if plot:
            logger.debug("Plotting")
            from qiskit.tools.visualization import plot_state_city
            plot_state_city(statevector)
    elif backend.name() in 'unitary_simulator':
        unitary = result.get_unitary(qc)
        logger.info("Circuit unitary is:\n{0}".format(unitary))
    else:  # For qasm and real devices
        counts = result.get_counts(qc)
        logger.info("{0} results: \n {1}".format(len(counts), counts))
        max_val = max(counts.values())
        max_val_status = max(counts, key=lambda key: counts[key])
        logger.info(
            "Max value is {0} ({2:4.2f} accuracy) for status {1}".format(
                max_val, max_val_status, max_val / 8192))
        if plot:
            logger.debug("Plotting")
            from qiskit.tools.visualization import plot_histogram
            plot_histogram(counts)
    logger.info("H was\n{0}".format(h))
    logger.info("Syndrome was\n{0}".format(syndrome))
    drawing_at_end(qc, args)


if __name__ == "__main__":
    main()
