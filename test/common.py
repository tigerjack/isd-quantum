import unittest
import logging
from os import getenv


class BasicTestCase(unittest.TestCase):
    SLOW_TEST = int(getenv('SLOW_TEST', '0'))

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(cls.__name__)
        cls.draw = False
        if getenv('LOG_LEVEL'):
            logging_level = logging._nameToLevel.get(
                getenv('LOG_LEVEL'), 'INFO')
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(module)-4s %(levelname)-8s %(funcName)-12s %(message)s')
            handler.setFormatter(formatter)
            cls.logger.addHandler(handler)
            cls.logger.setLevel(logging_level)

        cls.logger.warning("SLOW_TEST is {}".format(
            "ON, tests may take a long time" if cls.
            SLOW_TEST else "OFF, enable it using SLOW_TEST env variable"))
