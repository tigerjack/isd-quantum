from math import log


def boh(n):
    # 0 4, 1 5, 2 6, 3 7-->                 0, 8, +4
    # 0 2, 1 3 | 4 6, 5 7 -->         0, 4, +2 |            4, 8, +2
    # 0 1 || 2 3 || 4 5 || 6 7 --> 0, 2, +1 | 2, 4, +1 || 4, 6, +1 | 6, 8, +1
    bla3(0, n, int(n / 2), 1)
    print("***************")
    bla4(0, n, int(n / 2), 1)
    print("***************")


#start included, end excluded
def bla(start, end, swap_step):
    print("Start: {0}, end: {1}, swap_step: {2}".format(start, end, swap_step))
    if (swap_step == 0):
        print("End recursion")
        return
    for i in range(start, end - swap_step):
        print("***Cswapping {0} w/ {1}".format(i, i + swap_step))
    bla(start, int(end / 2), int(swap_step / 2))
    bla(int(end / 2) + 1, end, int(swap_step / 2))


def bla2(n):
    depth = log(n, 2)
    step = n / 2
    nn = n
    step = 1
    for i in range(depth):
        for j in range(0, nn / 2, step):
            print("***Cswapping {0} w/ {1}".format(j, j + swap_step))
        nn = nn / 2


def bla3(start, end, swap_step, counter):
    # print("{3} Start: {0}, end: {1}, swap_step: {2}".format(
    #     start, end, swap_step, ">" * counter))
    if (swap_step == 0 or start >= end):
        # print("End recursion")
        return
    for i in range(start, int((start + end) / 2)):
        print("***** Cswapping {0} w/ {1}".format(i, i + swap_step))
    bla3(start, int((start + end) / 2), int(swap_step / 2), counter + 1)
    bla3(int((start + end) / 2), end, int(swap_step / 2), counter + 1)


def bla4(start, end, swap_step, counter):
    print("{3} Start: {0}, end: {1}, swap_step: {2}".format(
        start, end, swap_step, ">" * counter))
    if (swap_step == 0 or start >= end):
        print("End recursion")
        return
    bla4(int((start + end) / 2), end, int(swap_step / 2), counter + 1)
    bla4(start, int((start + end) / 2), int(swap_step / 2), counter + 1)
    for i in range(int((start + end) / 2) - 1, start - 1, -1):
        print("***** Cswapping {0} w/ {1}".format(i, i + swap_step))


def bleah():
    from qiskit import QuantumCircuit, QuantumRegister
    from qiskit.tools.visualization import circuit_drawer
    qr1 = QuantumRegister(1, 'q1')
    qr2 = QuantumRegister(2, 'q2')
    qr3 = QuantumRegister(3, 'q3')
    qr4 = QuantumRegister(4, 'q4')
    qc = QuantumCircuit(qr1, qr2, qr3, qr4)
    qc_un = QuantumCircuit(qr1, qr2, qr3, qr4)

    import composed_gates as cg
    a, anc = cg.n_control_compute_2(qc, None, qr1, qr2, qr3, qr4)
    # a, anc = cg.n_control_compute_2(qc, None, qr2)
    # a, anc = cg.n_control_compute_2(qc, None, qr3)

    print(a)
    circuit_drawer(qc, filename="img/test.png")
    print("*********UNCOMPUTE************")

    return
    qc_un.add_register(anc)
    a, anc = cg.n_control_uncompute_2(qc_un, anc, qr1, qr2, qr3, qr4)
    # a, anc = cg.n_control_uncompute_2(qc, anc, qr2)
    # a, anc = cg.n_control_compute_2(qc, anc, qr3)
    print(a)
    circuit_drawer(qc_un, filename="img/test_un.png")


def main():
    # n = 8
    # boh(n)
    bleah()


if __name__ == "__main__":
    main()
