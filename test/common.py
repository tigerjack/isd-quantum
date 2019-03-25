import unittest
import logging
import os
import inspect
import time
from datetime import datetime


class BasicTestCase(unittest.TestCase):
    SLOW_TEST = int(os.getenv('SLOW_TEST', '0'))

    def setUp(self):
        self._started_at = time.time()

    def tearDown(self):
        elapsed = time.time() - self._started_at
        if elapsed > 5.0:
            print('({:.2f}s)'.format(round(elapsed, 2)), flush=True)

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(cls.__name__)

        cur_file = inspect.getfile(cls)
        cls.dirName = os.path.dirname(cur_file)
        cls.fileName = os.path.splitext(os.path.basename(cur_file))[0]
        cls.moduleName = os.path.splitext(cur_file)[0]

        # cls.draw = False
        if os.getenv('LOG_LEVEL'):
            logging_level = logging._nameToLevel.get(
                os.getenv('LOG_LEVEL'), 'INFO')
            # Disabled stream handler for now
            # handler = logging.StreamHandler()
            # formatter = logging.Formatter(
            #     '%(module)-4s %(levelname)-8s %(funcName)-12s %(message)s')
            # handler.setFormatter(formatter)
            # cls.logger.addHandler(handler)
            # cls.logger.setLevel(logging_level)

            # Set up the file handler.
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_name = os.path.join(cls.dirName, 'logs',
                                         '{}_{}.log'.format(cls.fileName, now))
            log_fmt = ('%(asctime)s:%(module)s.%(funcName)s:%(levelname)s:'
                       ' %(message)s')
            formatter = logging.Formatter(log_fmt)
            handler = logging.FileHandler(log_file_name)
            handler.setFormatter(formatter)
            cls.logger.addHandler(handler)
            cls.logger.setLevel(logging_level)
            if os.getenv('LOG_CLI'):
            # Disabled stream handler for now
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(module)-4s %(levelname)-8s %(funcName)-12s %(message)s')
                handler.setFormatter(formatter)
                cls.logger.addHandler(handler)
                cls.logger.setLevel(logging_level)

        cls.logger.warning("SLOW_TEST is {}".format(
            "ON, tests may take a long time" if cls.
            SLOW_TEST else "OFF, enable it using SLOW_TEST env variable"))
