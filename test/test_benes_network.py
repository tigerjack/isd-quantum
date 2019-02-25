import logging
from parameterized import parameterized
from math import log, ceil
from test.common import BasicTestCase
from isdquantum.circuit import hamming_weight_generate as hwg
from isdclassic.utils import rectangular_codes_hardcoded as rch


class BenesNetworkTestCase(BasicTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        perm_logger = logging.getLogger('isdquantum.circuit.hamming_weight')
        perm_logger.setLevel(cls.logger.level)
        perm_logger.handlers = cls.logger.handlers

    # Support method to compare
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
        self.logger.debug(
            "swaps_step_pattern is {0}".format(swaps_step_pattern))
        self.n_flips = sum(swaps_step_pattern)
        self.logger.debug("n_flips is {0}".format(sum(swaps_step_pattern)))

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
        self._init_swaps_per_step_pattern(n, w)
        pattern = hwg.generate_qubits_with_given_weight_benes_get_pattern(n, w)
        try:
            self.assertEqual(self.n_flips, len(pattern['swaps_pattern']))
        except:
            self.logger.error(pattern['swaps_pattern'])
            raise
