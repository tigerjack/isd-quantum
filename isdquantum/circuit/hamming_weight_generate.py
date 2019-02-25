import logging
from math import ceil, log

logger = logging.getLogger(__name__)


def generate_bits_from_flip_states(benes_pattern_dict, flip_states):
    arr = [0] * benes_pattern_dict['n_lines']
    for i in range(benes_pattern_dict['to_negate_range']):
        arr[i] = 1
    for i in benes_pattern_dict['swaps_pattern']:
        if (flip_states[i[0]][1] > 0.55):
            arr[i[1]], arr[i[2]] = arr[i[2]], arr[i[1]]
    return arr


def generate_qubits_with_given_weight_benes(circuit, a_qs, flip_qs,
                                            benes_pattern_dict):
    assert len(a_qs) == benes_pattern_dict['n_lines']
    assert len(flip_qs) == benes_pattern_dict['n_flips']
    for i in range(benes_pattern_dict['to_negate_range']):
        circuit.x(a_qs[i])
    for i in benes_pattern_dict['swaps_pattern']:
        circuit.cswap(flip_qs[i[0]], a_qs[i[1]], a_qs[i[2]])
    if benes_pattern_dict['negated_permutation']:
        circuit.x(a_qs)


def generate_qubits_with_given_weight_benes_i(circuit, a_qs, flip_qs,
                                              benes_pattern_dict):
    assert len(a_qs) == benes_pattern_dict['n_lines']
    assert len(flip_qs) == benes_pattern_dict['n_flips']
    if benes_pattern_dict['negated_permutation']:
        circuit.x(a_qs)
    for i in benes_pattern_dict['swaps_pattern'][::-1]:
        circuit.cswap(flip_qs[i[0]], a_qs[i[1]], a_qs[i[2]])
    for i in range(benes_pattern_dict['to_negate_range'])[::-1]:
        circuit.x(a_qs[i])


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
def generate_qubits_with_given_weight_benes_get_pattern(n, r):
    nwr_dict = {}
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
