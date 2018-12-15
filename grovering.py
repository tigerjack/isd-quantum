from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister
import numpy as np


def random_input(n, w):
    arr = np.zeros(n)
    arr[:w] = 1
    np.random.shuffle(arr)
    return arr


def from_arr_to_qubits(arr):
    qr = QuantumRegister(len(arr), 'selectors')
    qc = QuantumCircuit(qr)
    for i in range(len(arr)):
        if arr[i]:
            qc.x(qr[i])
    return qr, qc


def grover(qc, selectors, results, n, r, w):
    """
    Build the circuit composed by the oracle black box and the other quantum gates.
    :param n: The number of qubits (not including the ancillas)
    :param oracles: A list of black box (quantum) oracles; each of them selects a specific state
    :returns: The proper quantum circuit
    :rtype: qiskit.QuantumCircuit
    """
    # Add ancillas needed for multicontrolled cnots
    if (r > 2):
        ancillas = QuantumRegister(r - 1, 'nczancillas')
        qc.add(ancillas)
        # qc.add_register(ancillas)
        print("added multi-cz ancillas")
    else:
        ancillas = None
        print("NO ancillas")

    # Grover's algorithm is a repetition of an oracle box and a diffusion box.
    # The number of repetitions is given by the following formula.
    # We don't need all the 2**n possible states, only the ncr(n, w) ones (7 for a 7,4,3 with weight w=1)
    from math import pi, sqrt
    from scipy.special import binom
    n_states = binom(n, w)
    rep = int(round((pi / 2 * sqrt(n_states) - 1) / 2))
    print("n is {0}, n_states are {1}".format(n, n_states))
    print("Repetition of ORACLE+DIFFUSION boxes required: {0}".format(rep))
    for j in range(rep):
        negating_right_state(qc, selectors, results, n, r, ancillas)
        diffusion(n, selectors, qc)

    return qc


def diffusion(n, qr, qc):
    """
    The Grover diffusion operator.
    Given the arry of qiskit QuantumRegister qr and the qiskit QuantumCircuit qc, it adds the diffusion operator to the appropriate qubits in the circuit.
    """
    pass
    # for j in range(n):
    #     qc.h(qr[j])

    # # D matrix, flips state |000> only (instead of flipping all the others)
    # for j in range(n):
    #     qc.x(qr[j])
    # # 0..n-2 control bits, n-1 target, n..
    # if n > 3:
    #     import composed_gates
    #     composed_gates.n_controlled_Z_circuit(
    #         qc, [qr[j] for j in range(n - 1)], qr[n - 1],
    #         [qr[j] for j in range(n, n + n - 1)])
    # else:
    #     composed_gates.n_controlled_Z_circuit(
    #         qc, [qr[j] for j in range(n - 1)], qr[n - 1], None)

    # for j in range(n):
    #     qc.x(qr[j])
    # for j in range(n):
    #     qc.h(qr[j])


def negating_right_state(qc, selectors, result, n, r, ancillas):
    import composed_gates as cg

    for i in range(n):
        cg.n_controlled_Z_circuit(qc, [result[j] for j in range(r)],
                                  selectors[i], ancillas)
        qc.barrier()


def run():
    n = 7
    r = 3
    w = 1
    k = n - r

    arr = random_input(n, w)
    print("Random input is\n{0}".format(arr))
    sum_of_cols = np.array([1, 1, 1])

    selectors, qc = from_arr_to_qubits(arr)

    # Assuming all previous results are 1
    prev_res = QuantumRegister(r, 'prevresult')
    qc.add(prev_res)
    # qc.add_register(prev_res)
    qc.x(prev_res)

    grover(qc, selectors, prev_res, n, r, w)

    from os import sys
    # 1 online, 0 offline
    global online
    online = int(sys.argv[1])
    # 1 draw, 0 not draw
    draw = int(sys.argv[2])

    if (online == 0):
        print("Local qasm simulator")
        result_r = ClassicalRegister(n, 'result_col')
        qc.add(result_r)
        # qc.add_register(result_r)
        qc.measure(selectors, result_r)
        from qiskit import Aer
        backend = Aer.get_backend('qasm_simulator')
    elif (online == 1):
        print("Online qasm simulator")
        result_r = ClassicalRegister(n, 'result_col')
        qc.add(result_r)
        # qc.add_register(result_r)
        qc.measure(selectors, result_r)
        from qiskit import IBMQ
        IBMQ.load_accounts()
        backend = IBMQ.get_backend('ibmq_qasm_simulator')
    else:
        print("Local statevector simulator")
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
    if (online == 1 or online == 0):
        print("Printing counts")
        counts = result.get_counts(qc)
        print(counts)
        print(len(counts))
    #Statevector simulator
    else:
        print("Printing state")
        state = result.get_statevector(qc)
        print(state)


def main():
    run()


online = None
if __name__ == "__main__":
    main()
