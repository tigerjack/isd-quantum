import numpy as np
from isdquantum.methods.circuits.bruteforce_circ import BruteforceISDCircuit
from isdquantum.utils import qiskit_support
from isdquantum.utils import qiskit_support
from isdquantum.circuit import hamming_weight_generate as hwg


def get_fixed_1():
    w = 2
    h = np.array([
        [1, 0, 0, 1, 0, 0, 0, 0],
        [0, 1, 1, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 1, 1],
    ])
    syndromes = np.array([
        [1, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 1, 1, 0],
        [1, 0, 0, 1],
    ])
    errors = np.array([
        [1, 1, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 1, 0],
        [0, 1, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0],
    ])
    idx = 0
    return h, w, syndromes[idx], errors[idx]


# Try to launch quantum algorithm with a specific V obtained from classical algorithm
# for which we are sure that there exist a correct error
def ex_fixed(n, mode):
    print(n, mode)
    if n == 1:
        h, w, syndrome, exp_error = get_fixed_1()
    else:
        raise Exception("Unsopported n")

    shots = 4098
    r = h.shape[0]
    n = h.shape[1]
    k = n - r
    print("s = {}".format(syndrome))
    # bru = BruteforceAlg(h, syndrome, w, True, 'advanced', mode)
    bruci = BruteforceISDCircuit(h, syndrome, w, True, 'advanced', mode, None)
    qc = bruci.build_circuit()
    print("N qubits {}".format(qc.width()))
    # backend_name = 'statevector_simulator'
    backend_name = 'qasm_simulator'
    if backend_name == 'statevector_simulator':
        backend = qiskit_support.get_backend('aer', backend_name, qc.width())
        result = qiskit_support.run(qc, backend, shots=1)
        statevector = result.get_statevector()
        statevector_results = qiskit_support.from_statevector_to_prob_and_phase_detailed(
            statevector, qc)
        for k, v in statevector_results.items():
            print("{}".format(k))
            for kk, vv in v.items():
                print("\t{} {}".format(kk, vv))
        return
    else:  # QASM
        shots = 4096
        backend = qiskit_support.get_backend('aer', backend_name, qc.width())
        result = qiskit_support.run(qc, backend, shots=shots)
        counts = result.get_counts()
        print(counts)

        per_reg_c = qiskit_support.from_global_counts_to_per_register_count(
            counts, len(bruci._benes_flip_q), len(bruci._selectors_q))
        print("Per register count", per_reg_c)
        per_reg_p = qiskit_support.from_global_counts_to_per_register_prob(
            counts, len(bruci._benes_flip_q), len(bruci._selectors_q))
        print("Per register prob", per_reg_p)

        # print("Variance of counts", np.var(list(counts.values())))
        # top_counts = qiskit_support.get_top_percentile_from_counts(counts, 95)
        # print("top counts", top_counts)
        # first_status = next(iter(top_counts))
        # print("first status", first_status)
        # first_status_dict = {first_status: top_counts[first_status]}
        # print("first status dict", first_status_dict)
        # cregs_probs = qiskit_support.from_global_counts_to_per_register_prob(
        #     first_status_dict, *bruci.to_measure)
        # print("cregs probs", cregs_probs)
        # comb = hwg.generate_bits_from_flip_states(bruci._benes_dict,
        #                                           cregs_probs[0])
        # print("comb", comb)
        flips_comb = qiskit_support.from_register_prob_to_state(per_reg_p[0])
        selectors_comb = qiskit_support.from_register_prob_to_state(
            per_reg_p[1])
        print("flip comb", flips_comb)
        print("selectors comb", selectors_comb)
        if '?' in selectors_comb:
            selectors_generated_comb = hwg.generate_bits_from_flip_states(
                bruci._benes_dict, per_reg_p[0])
            print("selectors from flip comb is", selectors_generated_comb)

        print("exp error", exp_error)
        return


def main():
    ex_fixed(1, 'benes')
    # for m in ('benes', 'fpc'):
    for m in ['benes']:
        for j in range(1, 2):
            ex_fixed(j, m)
            print("**************************")
    # for j in range(1, 7):
    #     ex_fixed(j, 'fpc')
    #     print("**************************")
    # ex_w_classic()


if __name__ == "__main__":
    import logging
    logger = logging.getLogger("isdquantum.methods.circuits")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(module)-4s %(levelname)-8s %(funcName)-12s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    main()
