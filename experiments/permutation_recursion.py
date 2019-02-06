from math import ceil, log
import logging

_logger = logging.getLogger(__name__)


def permutation_pattern(self):
    self.permutation = {}
    steps = ceil(log(self.n, 2))
    self.permutation['n_selectors'] = 2**steps
    self.permutation['swaps_qubits_pattern'] = []
    if (self.w == 0 or self.w == self.permutation['n_selectors']):
        raise Exception("No combination is possible")

    # bcz ncr(8;5) == ncr(8;3)
    if self.w > self.permutation[
            'n_selectors'] / 2 and not self.w == self.permutation[
                'n_selectors']:
        initial_swaps = self.permutation['n_selectors'] - self.w
    else:
        initial_swaps = self.w

    _permutation_pattern_support(self, 0, initial_swaps,
                                 int(self.permutation['n_selectors'] / 2), 0)
    self.permutation['n_flips'] = len(self.permutation['swaps_qubits_pattern'])


def _permutation_pattern_support(self, start, end, swap_step, flip_q_idx):
    _logger.debug("Start: {0}, end: {1}, swap_step: {2}".format(
        start, end, swap_step))
    if (swap_step == 0 or start >= end):
        _logger.debug("Base case recursion")
        return flip_q_idx

    for_iter = 0
    for i in range(start, end):
        for_iter += 1
        _logger.info("cswap({2}, {0}, {1})".format(i, i + swap_step,
                                                   flip_q_idx))
        self.permutation['swaps_qubits_pattern'].append((flip_q_idx, i,
                                                         i + swap_step))
        flip_q_idx += 1

    for_iter_next = min(for_iter, int(swap_step / 2))
    _logger.debug(
        "Before recursion 1, start: {0}, end: {1}, swap_step: {2}, for_iter_next"
        .format(start, end, swap_step, for_iter_next))
    flip_q_idx = _permutation_pattern_support(self, start,
                                              start + for_iter_next,
                                              int(swap_step / 2), flip_q_idx)

    _logger.debug(
        "Before recursion, start: {0}, end: {1}, swap_step: {2}, for_iter_next {3}"
        .format(start, end, swap_step, for_iter_next))
    flip_q_idx = _permutation_pattern_support(
        self, start + swap_step, start + swap_step + for_iter_next,
        int(swap_step / 2), flip_q_idx)
    return flip_q_idx


def _permutation(self):
    _logger.info("Swaps pattern {0}".format(self.swaps_pattern))
    # Hadamard all ancillas
    self.circuit.h(self.flip_q)
    self.circuit.barrier()
    _permutation_support(self, 0, self.n, int(self.n / 2), 0, 0, False)
    self.circuit.barrier()


def _permutation_support(self, start, end, swap_step, swaps_pattern_idx,
                         flip_q_idx, divide):
    _logger.debug(
        "Start: {0}, end: {1}, swap_step: {2}, swap_pattern_idx: {3}, divide: {4}"
        .format(start, end, swap_step, swaps_pattern_idx, divide))
    ancilla_step = 0
    if (swap_step == 0 or start >= end):
        _logger.debug("Base case recursion")
        _logger.debug("<" * swaps_pattern_idx)
        return flip_q_idx
    for i in range(start, int((start + end) / 2)):
        _logger.info("Cswapping {0} & {1} using flip_q {2}".format(
            i, i + swap_step, flip_q_idx))
        self.circuit.cswap(self.flip_q[flip_q_idx], self.selectors_q[i],
                           self.selectors_q[i + swap_step])
        flip_q_idx += 1
        ancilla_step += 1
        for_exit_condition = (
            not divide
            and self.swaps_pattern[swaps_pattern_idx] == ancilla_step) or (
                divide
                and self.swaps_pattern[swaps_pattern_idx] / 2 == ancilla_step)
        if for_exit_condition:
            _logger.debug("exiting for bcz of swaps pattern")
            break
    swaps_pattern_idx += 1
    _logger.debug(">" * swaps_pattern_idx + "1")
    flip_q_idx = _permutation_support(self, start, int((start + end) / 2),
                                      int(swap_step / 2), swaps_pattern_idx,
                                      flip_q_idx, True)

    _logger.debug(">" * swaps_pattern_idx + "2")
    flip_q_idx = _permutation_support(self, int((start + end) / 2), end,
                                      int(swap_step / 2), swaps_pattern_idx,
                                      flip_q_idx, True)
    return flip_q_idx


def _permutation_support_i(self, start, end, swap_step, swaps_pattern_idx,
                           flip_q_idx, divide):
    _logger.debug(">" * (len(self.swaps_pattern) - swaps_pattern_idx))
    _logger.debug(
        "Start: {0}, end: {1}, swap_step: {2}, swap_pattern_idx: {3}, flip_q_idx: {4}, divide: {5}"
        .format(start, end, swap_step, swaps_pattern_idx, flip_q_idx, divide))
    if (swap_step == 0 or start >= end):
        _logger.debug("Base case recursion")
        _logger.debug("<" * (len(self.swaps_pattern) - swaps_pattern_idx))
        return flip_q_idx
    ancilla_step = 0
    _logger.debug("1st recursion")
    # if self.swaps_pattern[swaps_pattern_idx + 1] > self.max_swaps_per_step / 2:
    flip_q_idx = _permutation_support_i(self, int(
        (start + end) / 2), end, int(swap_step / 2), swaps_pattern_idx + 1,
                                        flip_q_idx, True)
    _logger.debug(">" * (len(self.swaps_pattern) - swaps_pattern_idx - 1) +
                  "...")

    _logger.debug("2nd recursion")
    flip_q_idx = _permutation_support_i(self, start, int(
        (start + end) / 2), int(swap_step / 2), swaps_pattern_idx + 1,
                                        flip_q_idx, True)
    _logger.debug(">" * (len(self.swaps_pattern) - swaps_pattern_idx - 1) +
                  "...")

    range_start = int((start + end) / 2) - 1
    #- self.max_swaps_per_step + self.swaps_pattern[swaps_pattern_idx]
    range_end = start - 1
    #- self.max_swaps_per_step + self.swaps_pattern[swaps_pattern_idx]
    _logger.debug("start {0}, end {1}".format(start, end))
    _logger.debug("swap at step {0}".format(
        self.swaps_pattern[swaps_pattern_idx]))
    _logger.debug("range start {0}, range end {1}".format(
        range_start, range_end))
    for i in range(range_start, range_end, -1):
        _logger.info("Cswapping {0} & {1} using flip_q {2}".format(
            i, i + swap_step, flip_q_idx))
        self.circuit.cswap(self.flip_q[flip_q_idx], self.selectors_q[i],
                           self.selectors_q[i + swap_step])
        flip_q_idx -= 1
        ancilla_step += 1
        for_exit_condition = (
            not divide
            and self.swaps_pattern[swaps_pattern_idx] == ancilla_step) or (
                divide
                and self.swaps_pattern[swaps_pattern_idx] / 2 == ancilla_step)
        if for_exit_condition:
            _logger.debug("exiting for bcz of swaps pattern")
            break
    _logger.debug("<" * (len(self.swaps_pattern) - swaps_pattern_idx - 1))
    return flip_q_idx


def _permutation_i(self):
    _logger.info("Swaps pattern {0}".format(self.swaps_pattern))
    _logger.debug("Max swaps per step {0}".format(self.max_swaps_per_step))
    _permutation_support_i(self, 0, self.n, int(self.n / 2), 0,
                           len(self.flip_q) - 1, False)
    self.circuit.barrier()
    # Hadamard all ancillas
    self.circuit.h(self.flip_q)
    self.circuit.barrier()
