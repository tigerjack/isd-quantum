import logging
import numpy as np
from math import isclose
logger = logging.getLogger(__name__)

# TODO rename misc to qiskit_utils


def from_statevector_to_prob_and_phase(statevector, qc):
    results = {}
    for i, v in enumerate(statevector):
        prob = np.linalg.norm(v)**2
        if isclose(prob, 0, abs_tol=1e-5):
            continue
        state = bin(i)[2:].zfill(qc.width())
        phase = np.angle(v, deg=True)
        phase_str = "{:3.4f}".format(phase)
        prob_str = "{:.4f}".format(prob)
        results[state] = {'phase': phase_str, 'prob': prob_str}
    return results


def from_statevector_to_prob_and_phase_detailed(statevector, qc):
    results = {}
    for i, v in enumerate(statevector):
        qregs_states = {}
        prob = np.linalg.norm(v)**2
        if isclose(prob, 0, abs_tol=1e-5):
            continue
        state = bin(i)[2:].zfill(qc.width())
        prev_l = 0
        for qr in reversed(qc.qregs):
            l = len(qr)
            st = state[prev_l:prev_l + l]
            qregs_states[qr.name] = st
            prev_l += l

        phase = np.angle(v, deg=True)
        prob_str = "{:.4f}".format(prob)
        phase_str = "{:3.4f}".format(phase)
        results[state] = {
            'phase': phase_str,
            'prob': prob_str,
            'detailed': qregs_states
        }
    return results


def get_backend(provider_name, backend_name, n_qubits):
    # logger.debug("real: {0}, online: {1}, backend_name: {2}".format(
    #     args.real, args.online, args.backend_name))

    if provider_name == "basicaer":
        from qiskit import BasicAer
        provider = BasicAer
    elif provider_name == "aer":
        from qiskit import Aer
        provider = Aer
    elif provider_name in ("projectqp", "projectqpprovider"):
        from qiskit_addon_projectq import ProjectQProvider
        provider = ProjectQProvider()
    elif provider_name in ("qcgpu", "qcgpuprovider"):
        from qiskit_qcgpu_provider import QCGPUProvider
        provider = QCGPUProvider()
    elif provider_name in ("jku", "jkuprovider"):
        from qiskit_addon_jku import JKUProvider
        provider = JKUProvider()
    elif provider_name in ("ibmq"):
        from qiskit import IBMQ
        IBMQ.load_accounts()
        provider = IBMQ
    else:
        raise Exception("Invalid provider {0}".format(provider_name))

    # only for real, online execution
    if backend_name == 'enough' and provider == 'ibmq':
        from qiskit.providers.ibmq import least_busy
        large_enough_devices = provider.backends(
            filters=lambda x: x.configuration(
            ).n_qubits >= n_qubits and x.configuration().simulator == False)
        backend = least_busy(large_enough_devices)
    else:
        backend = provider.get_backend(backend_name)
        if backend.configuration().n_qubits < n_qubits:
            raise Exception(
                "Backend {0} on provider {1} has only {2} qubits, while {3} are needed."
                .format(backend.name(), backend.provider(),
                        backend.configuration().n_qubits, n_qubits))
    return backend


def draw_circuit(qc, img_dir):
    logger.info("Drawing circuit")
    img_file = img_dir + qc.name
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


def draw_dag(qc, img_dir):
    logger.info("Drawing DAG")
    img_file = img_dir + qc.name + "_dag"
    from qiskit.converters import circuit_to_dag
    dag = circuit_to_dag(qc)
    from qiskit.tools.visualization import dag_drawer
    dag_drawer(dag, filename=img_file + ".png")


def get_compiled_circuit_infos(qc, backend):
    infos = {}
    logger.debug("Getting infos ... ")
    # backend_coupling = backend.configuration()['coupling_map']
    infos['n_qubits_qasm'] = qc.width()
    infos['depth_qasm'] = qc.depth()
    infos['count_ops'] = qc.count_ops()
    # infos['n_gates_qasm'] = sum(qc.count_ops().values())
    infos['n_gates_qasm'] = qc.size()
    infos['num_tensor_factors'] = qc.num_tensor_factors()
    # qc_qasm = qc.qasm()
    # infos['n_gates_qasm'] = len(qc_qasm.split("\n")) - 4
    # from qiskit import compile
    # qc_compiled = compile(qc, backend=backend)
    # qc_compiled_qasm = qc_compiled.experiments[0].header.compiled_circuit_qasm
    # infos['n_gates_compiled'] = len(qc_compiled_qasm.split("\n")) - 4
    return infos


def process_results(qc, result):
    if result.backend_name in 'statevector_simulator':
        statevector = result.get_statevector(qc)
        logger.info("State vector is\n{0}".format(statevector))
        logger.debug("Plotting")
        from qiskit.tools.visualization import plot_state_city
        plot_state_city(statevector)
    elif result.backend_name in 'unitary_simulator':
        unitary = result.get_unitary(qc)
        logger.info("Circuit unitary is:\n{0}".format(unitary))
    else:  # For qasm and real devices
        counts = result.get_counts(qc)
        logger.info("{0} results: \n {1}".format(len(counts), counts))
        logger.info("Time taken {}".format(result.time_taken))
        max_val = max(counts.values())
        max_val_status = max(counts, key=lambda key: counts[key])
        logger.info(
            "Max value is {0} ({2:4.2f} accuracy) for status {1}".format(
                max_val, max_val_status, max_val / 8192))
        logger.debug("Plotting")
        from qiskit.tools.visualization import plot_histogram
        plot_histogram(counts)


def export_circuit_to_qasm(qc, filename):
    q = qc.qasm()
    logger.debug("Exporing circuit")
    with open(filename, "w+") as f:
        f.write(q)


def run(qc, backend, shots=8192):
    logger.info(
        "Preparing execution with backend {0} from provider {1}".format(
            backend, backend.provider()))
    from qiskit import execute
    logger.debug("Execute")
    job = execute(qc, backend, shots=shots)
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
