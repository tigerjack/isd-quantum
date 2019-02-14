from math import ceil, log
import logging

logger = logging.getLogger(__name__)


# It allows to compute all combinations of length n and weight r,
# i.e. all combinations of length n w/ r bits set to 1.
def get_all_n_bits_weight_r(n, r, mode):
    if (mode == 'permutation'):
        return _ncr_permutation_pattern(n, r)
    else:
        raise Exception("Mode not implemented yet")


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
def _ncr_permutation_pattern(n, r):
    permutation_dict = {}
    steps = ceil(log(n, 2))
    permutation_dict['n_lines'] = 2**steps
    permutation_dict['swaps_pattern'] = []
    if (r == 0 or r == permutation_dict['n_lines']):
        raise Exception("No combination is possible")

    # bcz ncr(8;5) == ncr(8;3)
    if r > permutation_dict['n_lines'] / 2:
        initial_swaps = permutation_dict['n_lines'] - r
    else:
        initial_swaps = r

    _permutation_pattern_support(0, initial_swaps,
                                 int(permutation_dict['n_lines'] / 2), 0,
                                 permutation_dict)
    permutation_dict['n_flips'] = len(permutation_dict['swaps_pattern'])

    if (r > permutation_dict['n_lines'] / 2):
        permutation_dict['to_negate_range'] = permutation_dict['n_lines'] - r
        permutation_dict['negated_permutation'] = True
    else:
        permutation_dict['to_negate_range'] = r
        permutation_dict['negated_permutation'] = False
    return permutation_dict


def _permutation_pattern_support(start, end, swap_step, flip_q_idx,
                                 permutation_dict):
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
        permutation_dict['swaps_pattern'].append((flip_q_idx, i,
                                                  i + swap_step))
        flip_q_idx += 1

    for_iter_next = min(for_iter, int(swap_step / 2))
    logger.debug(
        "Before recursion 1, start: {0}, end: {1}, swap_step: {2}, for_iter_next"
        .format(start, end, swap_step, for_iter_next))
    flip_q_idx = _permutation_pattern_support(start, start + for_iter_next,
                                              int(swap_step / 2), flip_q_idx,
                                              permutation_dict)

    logger.debug(
        "Before recursion, start: {0}, end: {1}, swap_step: {2}, for_iter_next {3}"
        .format(start, end, swap_step, for_iter_next))
    flip_q_idx = _permutation_pattern_support(
        start + swap_step, start + swap_step + for_iter_next,
        int(swap_step / 2), flip_q_idx, permutation_dict)
    return flip_q_idx
