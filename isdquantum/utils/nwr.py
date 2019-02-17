from math import ceil, log
import logging
from isdquantum.utils import binary
from isdquantum.utils import adder

logger = logging.getLogger(__name__)


# It allows to compute all combinations of length n and weight r,
# i.e. all combinations of length n w/ r bits set to 1.
# benes
# fpt stands for fast population count
def get_all_n_bits_weight_r(n, r, mode):
    if (mode == 'benes'):
        return _benes_permutation_pattern(n, r)
    else:
        raise Exception("Mode not implemented yet")


def get_bits_weight_pattern(nbits):
    return _fpc_pattern(nbits)


# Return the list of qubits containing the result
def get_qubits_weight_circuit(circuit, a_qs, cin_q, cout_qs, nwr_dict):
    # nwr_dict = _fpc_pattern()
    # from qiskit import QuantumCircuit
    assert len(a_qs) == nwr_dict['n_lines']
    assert len(cin_q) == 1
    assert len(cout_qs) == nwr_dict['n_couts']
    for i in nwr_dict['adders_pattern']:
        cout_idx = int(i[-1][1])
        half_bits = int((len(i) - 1) / 2)
        input_qubits = []
        for j in i:
            if j[0] == 'a':
                input_qubits.append(a_qs[int(j[1])])
            elif j[0] == 'c':
                input_qubits.append(cout_qs[int(j[1])])
            else:
                raise Exception("Invalid")
        logger.debug("{0}".format([input_qubits[i] for i in range(half_bits)]))
        logger.debug("{0}".format(
            [input_qubits[i] for i in range(half_bits, 2 * half_bits)]))
        logger.debug("{0}".format([cout_qs[cout_idx]]))
        adder.adder_circuit(
            circuit, cin_q, [input_qubits[i] for i in range(half_bits)],
            [input_qubits[i]
             for i in range(half_bits, 2 * half_bits)], [cout_qs[cout_idx]])
    to_measure_qubits = []
    for j in nwr_dict['results']:
        if j[0] == 'a':
            to_measure_qubits.append(a_qs[int(j[1])])
        elif j[0] == 'c':
            to_measure_qubits.append(cout_qs[int(j[1])])
        else:
            raise Exception("Invalid")
    return to_measure_qubits


def get_qubits_weight_circuit_i(circuit, a_qs, cin_q, cout_qs, nwr_dict):
    # nwr_dict = _fpc_pattern()
    # from qiskit import QuantumCircuit
    assert len(a_qs) == nwr_dict['n_lines']
    assert len(cin_q) == 1
    assert len(cout_qs) == nwr_dict['n_couts']
    for i in nwr_dict['adders_pattern'][::-1]:
        cout_idx = int(i[-1][1])
        half_bits = int((len(i) - 1) / 2)
        input_qubits = []
        for j in i:
            if j[0] == 'a':
                input_qubits.append(a_qs[int(j[1])])
            elif j[0] == 'c':
                input_qubits.append(cout_qs[int(j[1])])
            else:
                raise Exception("Invalid")
        logger.debug("{0}".format([input_qubits[i] for i in range(half_bits)]))
        logger.debug("{0}".format(
            [input_qubits[i] for i in range(half_bits, 2 * half_bits)]))
        logger.debug("{0}".format([cout_qs[cout_idx]]))
        adder.adder_circuit_i(
            circuit, cin_q, [input_qubits[i] for i in range(half_bits)],
            [input_qubits[i]
             for i in range(half_bits, 2 * half_bits)], [cout_qs[cout_idx]])


def _fpc_pattern(n):
    nwr_dict = {'mode': 'fpc'}
    steps = ceil(log(n, 2))
    # TODO maybe we can use fewer lines
    # n_lines = n if n % 2 == 0 else n + 1
    n_lines = 2**steps
    nwr_dict['n_lines'] = n_lines
    nwr_dict['n_couts'] = n_lines - 1
    # couts = list(reversed(range(nwr_dict['n_couts'])))
    couts = ["c{0}".format(i) for i in range(nwr_dict['n_couts'])][::-1]
    # inputs = [chr(c) for c in range(ord('a'), ord('h') + 1)][::-1]
    inputs = ["a{0}".format(i) for i in range(nwr_dict['n_lines'])][::-1]
    # inputs = list(range(nwr_dict['n_lines']))
    logger.debug("inputs {0}".format(inputs))
    logger.debug("couts {0}".format(couts))
    nwr_dict['adders_pattern'] = []

    n_adders = n_lines
    n_inputs_per_adders = 0
    inputs_next_stage = inputs
    for i in range(steps):
        n_adders = int(n_adders / 2)
        n_inputs_per_adders += 2
        outputs_this_stage = []
        logger.debug("Stage {0}, n_adder {1}, n_inputs_per_adder {2}".format(
            i, n_adders, n_inputs_per_adders))
        logger.debug("inputs_next_stage {0}".format(inputs_next_stage))
        for j in range(n_adders):
            logger.debug("Stage {0}, adder {1}".format(i, j))
            adder_inputs = []
            for k in range(n_inputs_per_adders):
                adder_inputs.append(inputs_next_stage.pop())
            adder_cout = couts.pop()
            adder_outputs = adder_inputs[int(len(adder_inputs) /
                                             2):len(adder_inputs)] + [
                                                 adder_cout
                                             ]
            nwr_dict['adders_pattern'].append(
                tuple(adder_inputs) + tuple([adder_cout]))
            logger.debug("{0}, {1} --> {2}".format(adder_inputs, adder_cout,
                                                   adder_outputs))
            outputs_this_stage += adder_outputs
        inputs_next_stage = outputs_this_stage[::-1]
    logger.debug("adders pattern\n{0}".format(nwr_dict['adders_pattern']))
    nwr_dict['results'] = inputs_next_stage[::-1]
    logger.debug("results\n{0}".format(nwr_dict['results']))
    return nwr_dict


# Given how it's built, n should be a power of 2, or, at least,
# it returns the combination with n as power of 2.
# If the original n is not a power of 2, you may want to adapt the
# circuit avoiding the use of the last bits.
# Returns a dictionary containing the:
# 1. n_lines, the number of lines required,
# 2. n_flips, the number of fair coin flips required to obtain the full permutation
# 2. the swaps_pattern, i.e. a list of tuples containing:
#  - an integer signalling which flip to use
#  - the first line involved in the swap
#  - the second line involved in the swap
# 3. to_negate_range, i.e. which bits are initialized to 1 to apply the
#    permutation pattern
# 4. negated_permutation, a boolean signaling if the pattern is inversed
#    To reduce the number of flips, if r > (n/2), instead of initializing
#    r bits to 1 and then apply the permutation network, we initialize
#    n - r bits to 1 and apply the permutation network. In the latter case,
#    the obtained permutation should be negated.
def _benes_permutation_pattern(n, r):
    nwr_dict = {'mode': 'benes'}
    steps = ceil(log(n, 2))
    nwr_dict['n_lines'] = 2**steps
    nwr_dict['swaps_pattern'] = []
    if (r == 0 or r == nwr_dict['n_lines']):
        raise Exception("No combination is possible")

    # bcz ncr(8;5) == ncr(8;3)
    if r > nwr_dict['n_lines'] / 2:
        initial_swaps = nwr_dict['n_lines'] - r
    else:
        initial_swaps = r

    _benes_permutation_pattern_support(0, initial_swaps,
                                       int(nwr_dict['n_lines'] / 2), 0,
                                       nwr_dict)
    nwr_dict['n_flips'] = len(nwr_dict['swaps_pattern'])

    if (r > nwr_dict['n_lines'] / 2):
        nwr_dict['to_negate_range'] = nwr_dict['n_lines'] - r
        nwr_dict['negated_permutation'] = True
    else:
        nwr_dict['to_negate_range'] = r
        nwr_dict['negated_permutation'] = False
    return nwr_dict


def _benes_permutation_pattern_support(start, end, swap_step, flip_q_idx,
                                       nwr_dict):
    logger.debug("Start: {0}, end: {1}, swap_step: {2}".format(
        start, end, swap_step))
    if (swap_step == 0 or start >= end):
        logger.debug("Base case recursion")
        return flip_q_idx

    for_iter = 0
    for i in range(start, end):
        for_iter += 1
        logger.info("cswap({2}, {0}, {1})".format(i, i + swap_step,
                                                  flip_q_idx))
        nwr_dict['swaps_pattern'].append((flip_q_idx, i, i + swap_step))
        flip_q_idx += 1

    for_iter_next = min(for_iter, int(swap_step / 2))
    logger.debug(
        "Before recursion 1, start: {0}, end: {1}, swap_step: {2}, for_iter_next"
        .format(start, end, swap_step, for_iter_next))
    flip_q_idx = _benes_permutation_pattern_support(
        start, start + for_iter_next, int(swap_step / 2), flip_q_idx, nwr_dict)

    logger.debug(
        "Before recursion, start: {0}, end: {1}, swap_step: {2}, for_iter_next {3}"
        .format(start, end, swap_step, for_iter_next))
    flip_q_idx = _benes_permutation_pattern_support(
        start + swap_step, start + swap_step + for_iter_next,
        int(swap_step / 2), flip_q_idx, nwr_dict)
    return flip_q_idx


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    _fpc_pattern(4, 3)
