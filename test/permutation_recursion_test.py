import unittest
from os import getenv
import logging
from parameterized import parameterized
import mock
from experiments import permutation_recursion
from math import log, ceil


class PermutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # mock.Mock.permutation_pattern = permutation_recursion.permutation_pattern
        # mock.Mock._init_permutation_parameters = permutation_recursion._init_permutation_parameters
        # mock.Mock._init_required_permutation_selectors = permutation_recursion._init_required_permutation_selectors
        # mock.Mock._init_swaps_per_step_pattern = permutation_recursion._init_swaps_per_step_pattern
        # mock.Mock._init_required_flips = permutation_recursion._init_required_flips

        cls.logger = logging.getLogger(cls.__name__)
        if not getenv('LOG_LEVEL'):
            return
        logging_level = logging._nameToLevel.get(getenv('LOG_LEVEL'), 'INFO')

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(levelname)-8s %(funcName)-12s %(message)s')
        handler.setFormatter(formatter)
        cls.logger.addHandler(handler)
        cls.logger.setLevel(logging_level)

        perm_logger = logging.getLogger('experiments.permutation_recursion')
        perm_logger.addHandler(handler)
        perm_logger.setLevel(logging_level)

    @classmethod
    def tearDownClass(cls):
        pass
        # del mock.Mock.permutation_pattern
        # del mock.Mock._init_permutation_parameters
        # del mock.Mock._init_required_permutation_selectors
        # del mock.Mock._init_swaps_per_step_pattern
        # del mock.Mock._init_required_flips

    def setUp(self):
        self.prange_isd_mock = mock.Mock()

    # Support method
    def _init_swaps_per_step_pattern(self, n, w):
        steps = ceil(log(n, 2))
        selectors = 2**steps
        max_swaps_per_step = selectors / 2
        if (w > max_swaps_per_step):
            swaps_per_step_i = selectors - w
        else:
            swaps_per_step_i = w
        swaps_step_pattern = [swaps_per_step_i]
        for i in range(steps - 1):
            swaps_per_step_i = min(swaps_per_step_i * 2, max_swaps_per_step)
            swaps_step_pattern.append(swaps_per_step_i)
        # self.permutation['swaps_step_pattern'] = swaps_step_pattern
        self.logger.debug(
            "swaps_step_pattern is {0}".format(swaps_step_pattern))
        self.n_flips = sum(swaps_step_pattern)

    @parameterized.expand([
        ("n4w1", 4, 1),
        ("n4w2", 4, 2),
        ("n4w3", 4, 3),
        ("n7w1", 7, 1),
        ("n7w3", 7, 3),
        ("n8w1", 8, 1),
        ("n8w2", 8, 2),
        ("n8w3", 8, 3),
        ("n8w4", 8, 4),
        ("n16w1", 16, 1),
        ("n16w3", 16, 3),
        ("n16w4", 16, 4),
        ("n16w6", 16, 6),
        ("n32w3", 32, 3),
        ("n32w3", 32, 8),
        ("n33w3", 33, 3),
        ("n38w9", 38, 9),
        ("n45w11", 45, 11),
        ("n54w21", 54, 21),
        ("n64w33", 64, 23),
    ])
    def test_patterns(self, name, n, w):
        self.logger.info("")
        self._init_swaps_per_step_pattern(n, w)
        self.prange_isd_mock.n = n
        self.prange_isd_mock.w = w
        permutation_recursion.permutation_pattern(self.prange_isd_mock)
        try:
            self.assertEqual(
                self.n_flips,
                len(self.prange_isd_mock.permutation['swaps_qubits_pattern']))
        except:
            self.logger.error(
                self.prange_isd_mock.permutation['swaps_qubits_pattern'])
            raise
