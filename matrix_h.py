from qiskit import execute
from qiskit import IBMQ
# from qiskit.backends.ibmq import least_busy
from qiskit import Aer
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import numpy as np


def h743():
    print("Producing [7, 4, 3] matrix")
    h = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 0],
                  [0, 1, 0], [0, 0, 1]]).T
    return h


def produce_circuit_from_matrix(h):
    n = h.shape[1]
    r = h.shape[0]
    k = n - r
    # for i in range(n):
    #     s = 'col' + str(i)
    #     qrs.append(QuantumRegister(r, name=s))

    # + n for the ancillas used in the sum
    qr = QuantumRegister(n * r + r)
    cr = ClassicalRegister(n * r + r)
    qc = QuantumCircuit(qr, cr)
    for i in range(n):  # colums
        for j in range(r):  #rows
            if (h[j][i] == 1):
                # print("Storing 1 in qr{0}".format(r * i + j))
                qc.x(qr[r * i + j])
    return qc, qr, cr


def run_circuit(qc, qr, cr):
    for i in range(21, 24):
        qc.measure(qr, cr)
    # backend = Aer.get_backend('qasm_simulator')
    IBMQ.load_accounts()
    backend = IBMQ.get_backend(name="ibmq_qasm_simulator")

    from qiskit.tools.visualization import circuit_drawer
    circuit_drawer(qc, filename="test.png")
    print("Compiling")
    job = execute(qc, backend)
    print(job.job_id())
    result = job.result()
    print("Getting results, i.e. executing")
    counts = result.get_counts(qc)
    print(counts)


def sum_cols_0_1(qc, qr, cr):
    # Compute
    for i in range(3):
        qc.cx(qr[i], qr[i + 3])
    # Copy
    for i in range(3):
        # The ancillas are in qr[21] ..[22]
        qc.cx(qr[i + 3], qr[3 * 7 + i])
    # Uncompute
    for i in range(3):
        qc.cx(qr[i], qr[i + 3])


def main():
    h = h743()
    qc, qr, cr = produce_circuit_from_matrix(h)
    sum_cols_0_1(qc, qr, cr)
    run_circuit(qc, qr, cr)


if __name__ == "__main__":
    main()
