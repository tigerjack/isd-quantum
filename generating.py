import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister


# n is the original set of registers
def permutation(n, r):
    # Check if n is a power of 2
    isPower = ((n & (n - 1)) == 0) and n != 0

    # if n is not a power of 2
    if not (isPower):
        from math import ceil, log
        exponent = ceil(log(n, 2))
        nn = 2**exponent
    else:
        nn = n

    # The idea is to carry around the computation on nn registers and then
    # copy the results in the n registers
    computing_q = QuantumRegister(nn, 'q-com')
    ancilla_flip_q = QuantumRegister(1, 'q-ancf')
    ancilla_flip_c = ClassicalRegister(1, 'c-ancf')

    circuit = QuantumCircuit(computing_q, ancilla_flip_q, ancilla_flip_c)

    # Initialize r bits to 1, all the others to 0
    for i in range(r):
        circuit.x(computing_q[i])
    circuit.barrier()

    # Hadamard, this is our coin flip
    circuit.h(ancilla_flip_q)

    # TODO specialized for nn = 8, generalize
    last2 = round(n / 2)  # 4
    last4 = round(n / 4)  # 2

    for i in range(n - last2):
        print("cswapping {0} {1}".format(i, i + last2))
        circuit.cswap(ancilla_flip_q[0], computing_q[i],
                      computing_q[i + last2])
        circuit.measure(ancilla_flip_q, ancilla_flip_c)
        circuit.h(ancilla_flip_q)
    print("*******")
    circuit.barrier()

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

    for i in range(0, n - 1, 2):
        print("cswapping {0} {1}".format(i, i + 1))
        circuit.cswap(ancilla_flip_q[0], computing_q[i], computing_q[i + 1])
        circuit.measure(ancilla_flip_q, ancilla_flip_c)
        circuit.h(ancilla_flip_q)
    print("*******")
    circuit.barrier()

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

    # Two different ideas
    # IDEA 1
    # Bcz we only want 7 outputs out of 8, we copy the first 7 qubits
    # but only if the 8th qubit is 0.
    # In other words, we don't want to copy the results w/a 1 in the
    # 8th position.
    # One potential problem here is that ~1/8 of the results will be
    # all zeros; however, given that this results are selection lines,
    # maybe can be easily wrapped around.
    # Another great problem is that there are more qubits (+n) and
    # gates, so the computation is very slow.
    # TODO generalize
    # TODO maybe we can using a sort of Grover's algorithm to diminish
    # the amplitude on state 0000'0000

    # ancillas_res_q = QuantumRegister(n)
    # ancillas_res_c = ClassicalRegister(n)
    # circuit.add(ancilla_res_q)
    # circuit.add(ancilla_res_c)
    # circuit.x(computing_q[nn - 1])
    # for i in range(n):
    #     circuit.ccx(computing_q[nn - 1], computing_q[i], ancillas_res_q[i])

    # circuit.measure(ancillas_res_q, ancillas_res_c)
    # circuit.reset(ancilla_flip_q)
    # circuit.measure(ancilla_flip_q, ancilla_flip_c)
    # return circuit

    # IDEA2
    # Here instead the idea is to apply a cswap b/w the last bit and the first non zero
    # but only when the last bit is one.
    # The problem here is that the probabilities are not random anymore.
    # The advantage is that it is faster.

    # We first copy the last bit in ancilla_flip_q
    ancilla_one_q = QuantumRegister(1, 'q-ancone')
    circuit.add(ancilla_one_q)

    # Then if ancilla_flip is 1 (and so also ancilla_res[nn-1])
    # we swap this last qubit with the first non zero
    # Worst case 0000'0111
    for i in range(nn - r):
        circuit.reset(ancilla_flip_q)
        circuit.x(ancilla_one_q)
        circuit.ccx(ancilla_one_q[0], computing_q[nn - 1], ancilla_flip_q[0])
        circuit.cswap(ancilla_flip_q[0], computing_q[nn - 1], computing_q[i])
        circuit.barrier()

    computing_c = ClassicalRegister(n, 'c-com')
    circuit.add(computing_c)

    for i in range(n):
        circuit.measure(computing_q[i], computing_c[i])

    circuit.reset(ancilla_flip_q)
    circuit.measure(ancilla_flip_q, ancilla_flip_c)
    return circuit


def main():

    from os import sys
    # 1 online, 0 offline
    online = int(sys.argv[1])
    # 1 draw, 0 not draw
    draw = int(sys.argv[2])

    n = 7
    r = 3
    qc = permutation(n, r)

    if (draw == 1):
        print("Drawing")
        from qiskit.tools.visualization import circuit_drawer
        circuit_drawer(qc, filename='img/generating.png')

    if (online == 0):
        from qiskit import Aer
        backend = Aer.get_backend('qasm_simulator')
    else:
        from qiskit import IBMQ
        IBMQ.load_accounts()
        backend = IBMQ.get_backend('ibmq_qasm_simulator')

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


if __name__ == "__main__":
    main()
