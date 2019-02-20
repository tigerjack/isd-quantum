import numpy as np
from isdquantum.methods.lee_brickell import LeeBrickellISD
import itertools


def get_fixed_3():
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


# Try to launch quantum algorithm with a specific V obtained from classical algorithm
# for which we are sure that there exist a correct error
def ex_fixed():
    hr, v, perm, w, p, s_sig, exp_comb, exp_e_hat, exp_e = get_fixed_3()
    k = v.shape[0]
    wanted_sum = w - p
    print("v =\n{}".format(v))
    print("s_sig = ".format(s_sig))
    lb = LeeBrickellISD(hr, v, s_sig, w, p, True, 'advanced', 'benes')
    qc = lb.build_circuit()
    from qiskit import BasicAer, execute
    result = execute(qc, BasicAer.get_backend('qasm_simulator')).result()
    counts = result.get_counts()
    print(counts)

    # BUILD ERROR VECTOR
    max_val = max(counts.values())
    accuracy = max_val / 1024
    max_val_status = max(counts, key=lambda key: counts[key])
    error_positions = [
        pos for pos, char in enumerate(max_val_status[::-1]) if char == '1'
    ]
    print("Error positions {}".format(error_positions))
    print("Expected error positions {}".format(exp_comb))
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


def main():
    # ex_fixed_v()
    ex_fixed()


if __name__ == "__main__":
    main()
