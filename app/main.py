import argparse


def _usage():
    parser = argparse.ArgumentParser(
        description="Collection of isd algorithms for quantum computers")
    parser.add_argument('n', metavar='n', type=int, help='The n of the code')
    parser.add_argument('k', metavar='k', type=int, help='The k of the code.')
    parser.add_argument(
        'd', metavar='d', type=int, help='The hamming distance of the code.')
    parser.add_argument(
        'w', metavar='w', type=int, help='The weight of the error.')
    parser.add_argument(
        '--isd_mode',
        help='The isd choice',
        required=True,
        choices=['bruteforce', 'lee_brickell'],
    )
    parser.add_argument(
        '-p',
        type=int,
        help='The p for lee brickell',
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
        '--real',
        action='store_true',
        help=
        'Invoke the real quantum device (implies -o). Default is a simulator.')
    parser.add_argument(
        '--online',
        action='store_true',
        help=
        'Use the online IBMQ devices. Default is local (simulator). This option is automatically set to true when we want to use a real device (see -r).'
    )
    parser.add_argument(
        '--provider',
        # choices=['basicaer', 'aer', 'qcgpu', 'projectq', 'jku', 'ibmq'],
        help=
        "The name of the provider. At the moment, the available local providers are: BasicAer, Aer, QCGPU, ProjectQ, JKU, IBMQ. The default choices are IBMQ for online execution (see -o) and BasicAer for local execution."
    )
    parser.add_argument(
        '--backend',
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


def _clean_args(args):
    # if user wants a real simulator, then we should go online
    args.online = True if args.real else args.online
    # if user didn't provide a backend name, we impose a default one
    # The default choice is the 'qasm_simulator' for a simulation,
    # a large enough device for a real execution
    if args.backend is None:
        if args.online:
            if args.real:
                # enough means get a large enough device to run the circuit
                args.backend = 'enough'
            else:
                args.backend = 'ibmq_qasm_simulator'
        else:
            args.backend = 'qasm_simulator'
    # Same for providers
    # Default choices are IBMQ for online execution, BasicAer for offline.
    if args.provider is None:
        if args.online:
            args.provider = 'ibmq'
        else:
            from qiskit import BasicAer
            args.provider = 'basicaer'
    if (args.draw_circuit or args.draw_dag) and args.img_dir is None:
        args.img_dir = 'data/img/'
    if (args.isd_mode not in ('bruteforce') and args.p is None):
        raise Exception(
            "p must be specified for modes different from bruteforce")


def main():
    args = _usage()
    _clean_args(args)
    from app.session import Session
    session = Session()
    session.args = args
    from app import entry
    entry.go()


if __name__ == "__main__":
    main()
