import unittest
import logging


class BasicTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(cls.__name__)
        cls.draw = False
        from os import getenv
        if getenv('LOG_LEVEL'):
            logging_level = logging._nameToLevel.get(
                getenv('LOG_LEVEL'), 'INFO')
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(module)-4s %(levelname)-8s %(funcName)-12s %(message)s')
            handler.setFormatter(formatter)
            cls.logger.addHandler(handler)
            cls.logger.setLevel(logging_level)
