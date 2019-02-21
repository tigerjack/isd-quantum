import numpy as np
from isdquantum.methods.circuits.lee_brickell_bruteforce_circ import LeeBrickellCircuit
from isdclassic.utils import rectangular_codes_hardcoded as rch
from isdclassic.methods.lee_brickell import LeeBrickell
import itertools


def get_fixed_1():
    w = 2
    p = 1
    perm = np.array([
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
    ])
    hr = np.array([
        [0, 0, 1, 0, 1, 0, 0, 0],
        [1, 0, 1, 1, 0, 1, 0, 0],
        [1, 1, 0, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 0, 0, 0, 1],
    ])
    v = hr[:, 0:4]
    s_sig = np.array([1, 1, 0, 1])
    exp_combination = (3)
    exp_e_hat = [0, 0, 0, 1, 1, 0, 0, 0]
    exp_e = np.array([1, 0, 0, 0, 0, 0, 1, 0])
    return hr, v, perm, w, p, s_sig, exp_combination, exp_e_hat, exp_e


def get_fixed_2():
    w = 2
    p = 1
    perm = np.array([
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
    ])
    hr = np.array([
        [1, 0, 1, 1, 1, 0, 0, 0],
        [0, 1, 1, 0, 0, 1, 0, 0],
        [1, 1, 0, 0, 0, 0, 1, 0],
        [1, 0, 1, 1, 0, 0, 0, 1],
    ])
    v = hr[:, 0:4]
    s_sig = np.array([0, 0, 0, 1])
    # i.e. v[3] + s_sig should have weight w-p=1
    exp_combination = (3)
    exp_e_hat = [0, 0, 0, 1, 1, 0, 0, 0]
    exp_e = np.array([1, 0, 0, 0, 0, 0, 1, 0])

    return hr, v, perm, w, p, s_sig, exp_combination, exp_e_hat, exp_e


def get_fixed_3():
    w = 2
    p = 2
    perm = np.array([
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
    ])
    hr = np.array([
        [0, 1, 0, 0, 1, 0, 0, 0],
        [1, 1, 0, 1, 0, 1, 0, 0],
        [0, 1, 1, 1, 0, 0, 1, 0],
        [1, 1, 1, 1, 0, 0, 0, 1],
    ])
    v = hr[:, 0:4]
    s_sig = np.array([1, 0, 0, 0])
    exp_combination = [1, 3]
    exp_e_hat = np.array([0, 1, 0, 1, 0, 0, 0, 0])
    exp_e = np.array([1, 0, 0, 0, 0, 0, 1, 0])
    return hr, v, perm, w, p, s_sig, exp_combination, exp_e_hat, exp_e


def get_fixed_4():
    w = 2
    p = 1
    hr = np.array([
        [0, 0, 1, 0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 1, 0, 0],
        [1, 1, 1, 1, 0, 0, 1, 0],
        [1, 0, 1, 1, 0, 0, 0, 1],
    ])
    v = hr[:, 0:4]
    perm = np.array([
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
    ])
    s_sig = np.array([1, 1, 1, 0])
    exp_combination = [1]
    exp_e_hat = np.array([0, 1, 0, 0, 1, 0, 0, 0])
    exp_e = np.array([1, 1, 0, 0, 0, 0, 0, 0])

    return hr, v, perm, w, p, s_sig, exp_combination, exp_e_hat, exp_e


def get_fixed_5():
    w = 2
    p = 1
    perm = np.array([
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 0],
    ])
    hr = np.array([
        [1, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 1, 0, 0],
        [1, 1, 1, 1, 0, 0, 1, 0],
        [1, 1, 0, 1, 0, 0, 0, 1],
    ])
    v = hr[:, 0:4]
    s_sig = np.array([1, 1, 1, 0])
    exp_combination = [2]
    exp_e_hat = np.array([0, 0, 1, 0, 1, 0, 0, 0])
    exp_e = np.array([1, 1, 0, 0, 0, 0, 0, 0])

    return hr, v, perm, w, p, s_sig, exp_combination, exp_e_hat, exp_e


# Try to launch quantum algorithm with a specific V obtained from classical algorithm
# for which we are sure that there exist a correct error
def ex_fixed(n, mode):
    if n == 1:
        hr, v, perm, w, p, s_sig, exp_comb, exp_e_hat, exp_e = get_fixed_1()
    elif n == 2:
        hr, v, perm, w, p, s_sig, exp_comb, exp_e_hat, exp_e = get_fixed_2()
    elif n == 3:
        hr, v, perm, w, p, s_sig, exp_comb, exp_e_hat, exp_e = get_fixed_3()
    elif n == 4:
        hr, v, perm, w, p, s_sig, exp_comb, exp_e_hat, exp_e = get_fixed_4()
    elif n == 5:
        hr, v, perm, w, p, s_sig, exp_comb, exp_e_hat, exp_e = get_fixed_5()

    shots = 4098
    hr, v, perm, w, p, s_sig, exp_comb, exp_e_hat, exp_e = get_fixed_1()
    k = v.shape[0]
    wanted_sum = w - p
    print("v =\n{}".format(v))
    print("s_sig = {}".format(s_sig))
    lb = LeeBrickellCircuit(hr, v, s_sig, w, p, True, 'advanced', mode)
    qc = lb.build_circuit()
    from qiskit import BasicAer, execute
    result = execute(
        qc, BasicAer.get_backend('qasm_simulator'), shots=shots).result()
    counts = result.get_counts()
    print("{} counts\n{}".format(len(counts), counts))

    # BUILD ERROR VECTOR
    max_val = max(counts.values())
    print("max val", max_val)
    accuracy = max_val / shots
    print("Accuracy ", accuracy)
    max_val_status = max(counts, key=lambda key: counts[key])
    print("max val status ", max_val_status)
    error_positions = [
        pos for pos, char in enumerate(max_val_status[::-1]) if char == '1'
    ]
    print("Error positions {}".format(error_positions))
    print("Expected error positions {}".format(exp_comb))
    # print("Drawing")
    # from isdquantum.utils import misc
    # misc.draw_circuit(qc, 'data/img/exp/lee_fixed_{}_{}'.format(n, mode))
    v_extr = v[:, error_positions]
    sum_to_s = (v_extr.sum(axis=1) + s_sig) % 2
    sum_to_s_w = np.sum(sum_to_s)
    if sum_to_s_w != w - p:
        print("Error")  # We can't be here
        return
    else:
        print("Maybe found")  # Sure in this fixed example
    e_hat = np.concatenate((np.zeros(k), sum_to_s))
    print("e_hat before error position is {}".format(e_hat))
    for j in error_positions:
        e_hat[j] = 1
    print("e_hat after error position is {}".format(e_hat))
    print("expected e_hat is {}".format(exp_e_hat))
    e_hat_w = np.sum(e_hat)
    print("Weight of e_hat is {}".format(e_hat_w))
    if e_hat_w == w:
        print("FOUND!!")
    else:
        print("ERROR")  # Can't be here
        return
    e = np.mod(np.dot(e_hat, perm.T), 2)
    print("Error is {}".format(e))
    print("Expected error is {}".format(exp_e))


def ex_w_classic():
    n = 8
    k = 4
    d = 4
    w = 2
    p = 2
    h, _, syndromes, errors, w, _ = rch.get_isd_systematic_parameters(
        n, k, d, w)
    s = syndromes[1]
    lee = LeeBrickell(h, s, w, p)
    e = lee.run()
    for k, v in lee.result.items():
        print(k, v)
    print(e)
    # print(
    #         "Launching TEST w/ n = {0}, k = {1}, d = {2}, w = {3}, p = {4}".
    #         format(n, k, d, w, p))
    # print("h = \n{0}".format(h))


def main():
    # ex_fixed(1, 'fpc')
    ex_fixed(1, 'benes')
    # ex_w_classic()


if __name__ == "__main__":
    main()
