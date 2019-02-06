from math import ceil, log
import logging
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit import BasicAer
_logger = logging.getLogger(__name__)


# n choose w
def _get_required_ancilla_for_permutation(n, w):
    #TODO if w > n/2, use (w - n/2) and negation
    steps = ceil(log(n, 2))
    n_power2 = 2**steps
    max_swaps_per_step = int(n_power2 / 2)
    # swaps required at first steps is equal to weight
    swaps_per_step_i = w
    swaps_pattern = [w]
    for i in range(steps - 1):
        swaps_per_step_i = min(swaps_per_step_i * 2, max_swaps_per_step)
        swaps_pattern.append(swaps_per_step_i)
    return n_power2, swaps_pattern


def _permutation():
    _logger.info("Swaps pattern {0}".format(swaps_patterns))
    n = len(selectors_q)
    # Hadamard all ancillas
    circuit.h(flip_q)
    circuit.barrier()
    _permutation_support(0, 0, n, int(n / 2), False)
    circuit.barrier()


def _permutation_support(swaps_patterns_idx, start, end, swap_step, divide):
    _logger.debug(
        "Start: {0}, end: {1}, swap_step: {2}, swap_pattern_idx: {3}".format(
            start, end, swap_step, swaps_patterns_idx))
    # if (swap_step == 0 or start >= end):
    ancilla_step = 0
    if (swap_step == 0 or start >= end):
        # if (swap_step == 1):
        _logger.debug("Base case recursion")
        _logger.info("<" * swaps_patterns_idx)
        return
    for i in range(start, int((start + end) / 2)):
        flip_q_idx = flip_q_indexes.pop()
        _logger.info("Cswapping {0} & {1} using hadamard {2}".format(
            i, i + swap_step, flip_q_idx))
        circuit.cswap(flip_q[flip_q_idx], selectors_q[i],
                      selectors_q[i + swap_step])
        # if (np.random.rand() > 0.5):
        #     selectors_q[i], selectors_q[i + swap_step] = selectors_q[
        #         i + swap_step], selectors_q[i]
        ancilla_step += 1
        for_exit_condition = (
            not divide and swaps_patterns[swaps_patterns_idx] == ancilla_step
        ) or (divide
              and swaps_patterns[swaps_patterns_idx] / 2 == ancilla_step)
        if for_exit_condition:
            _logger.debug("exiting for bcz of swaps patterns")
            break
    # _logger.debug("Ancilla used after FOR {0}".format(ancilla_used))
    swaps_patterns_idx += 1
    _logger.info(">" * swaps_patterns_idx + "1")
    _permutation_support(swaps_patterns_idx, start, int((start + end) / 2),
                         int(swap_step / 2), True)

    # _logger.debug(
    # "Ancilla used after FIRST recursion {0}".format(ancilla_used))
    _logger.info(">" * swaps_patterns_idx + "2")
    _permutation_support(swaps_patterns_idx, int((start + end) / 2), end,
                         int(swap_step / 2), True)
    # _logger.debug(
    #     "Ancilla used after SECOND recursion {0}".format(ancilla_used))
    # return ancilla_used


def _permutation_i(circuit, selectors_q, flip_q, weight):
    n = len(selectors_q)
    _logger.debug("Permutation_i -> input n is {0}".format(n))
    ancilla_counter = len(flip_q)
    _logger.debug("Permutation_i -> Number of hadamard qubits is {0}".format(
        ancilla_counter))

    _permutation_support_i(circuit, selectors_q, flip_q, ancilla_counter - 1,
                           0, n, int(n / 2))
    circuit.barrier()
    # Hadamard all ancillas
    circuit.h(flip_q)
    circuit.barrier()


def _permutation_support_i(circuit, selectors_q, flip_q, ancilla_used, start,
                           end, swap_step):
    _logger.debug(
        "Permutation support_i -> Start: {0}, end: {1}, swap_step: {2}".format(
            start, end, swap_step))
    if (swap_step == 0 or start >= end):
        _logger.debug("Permutation support_i -> Base case recursion")
        return ancilla_used
    ancilla_used = _permutation_support_i(circuit, selectors_q,
                                          flip_q, ancilla_used,
                                          int((start + end) / 2), end,
                                          int(swap_step / 2))
    _logger.debug(
        "Permutation support_i -> Ancilla used after FIRST recursion {0}".
        format(ancilla_used))
    ancilla_used = _permutation_support_i(circuit, selectors_q, flip_q,
                                          ancilla_used, start,
                                          int((start + end) / 2),
                                          int(swap_step / 2))
    _logger.debug(
        "Permutation support_i -> Ancilla used after SECOND recursion {0}".
        format(ancilla_used))
    for i in range(int((start + end) / 2) - 1, start - 1, -1):
        _logger.debug(
            "Permutation support_i -> Cswapping {0} & {1} using hadamard {2}".
            format(i, i + swap_step, ancilla_used))
        circuit.cswap(flip_q[ancilla_used], selectors_q[i],
                      selectors_q[i + swap_step])
        ancilla_used -= 1
    _logger.debug("Permutation support_i -> Ancilla used after FOR {0}".format(
        ancilla_used))
    return ancilla_used


n = 8
w = 3
circuit = QuantumCircuit()
n_power2, swaps_patterns = _get_required_ancilla_for_permutation(n, w)
selectors_q = None
flip_q = None
flip_q_indexes = None


def main():
    # fake columns quantum register
    for i in range(20):
        global selectors_q
        # selectors_q = [1] * w + [0] * (n_power2 - w)
        _logger.debug(circuit.qregs)
        selectors_q = QuantumRegister(n_power2, 'cols_q')
        circuit.add_register(selectors_q)
        global flip_q
        # flip_q = [i for i in range(sum(swaps_patterns))]
        flip_q = QuantumRegister(sum(swaps_patterns), 'flip_q')
        circuit.add_register(flip_q)
        global flip_q_indexes
        flip_q_indexes = [i for i in range(sum(swaps_patterns))]

        for i in range(w):
            circuit.x(selectors_q[i])

        _permutation()
        # _logger.warning(selectors_q)
        cr = ClassicalRegister(selectors_q.size, 'cols_c')
        circuit.add_register(cr)
        circuit.measure(selectors_q, cr)
        backend = BasicAer.get_backend('qasm_simulator')
        job = execute(circuit, backend)
        counts = job.result().get_counts()
        _logger.info(counts)
        _logger.info(len(counts))
        from math import factorial
        _logger.info(factorial(n) / factorial(w) / factorial(n - w))
        _logger.info(circuit.width())


if __name__ == "__main__":
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    main()
