import logging
# from app import common
import os
from app.session import Session
from isdclassic.utils import rectangular_codes_hardcoded as rch
from random import randint

logger = logging.getLogger(__name__)


def go():
    _initialize_loggers()
    _get_sample_matrix_and_random_syndrome()
    ses = Session()
    if (ses.args.backend in ('statevector_simulator', 'unitary_simulator')):
        ses.need_measures = False
    else:
        ses.need_measures = True
    # TODO trying to split workflow
    if ses.args.isd_mode == 'bruteforce':
        from app import launch_bruteforce
        next_step = launch_bruteforce
        # next_app = BruteforceApp(h, syndrome, w, need_measures)
        # qc, backend = next_app.prepare_circuit_for_backend(
        #     args.mct_mode, args.nwr_mode, args.provider, args.backend)
    elif ses.args.isd_mode == 'lee_brickell':
        from app import launch_lee_brickell
        next_step = launch_lee_brickell
        # next_app = LeeBrickellApp(h, syndrome, w, p, need_measures)
        # qc, error, accuracy = next_app.run(args.mct_mode, args.nwr_mode,
        #                                    args.provider, args.backend)
    else:
        raise Exception("ISD mode not implemented yet {}".format(
            ses.args.isd_mode))
    next_step.go()


def _initialize_loggers():
    logging_level = logging._nameToLevel.get(os.getenv('LOG_LEVEL'), 'INFO')
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        # '%(asctime)s %(levelname)-8s %(name)-12s %(funcName)-12s %(message)s')
        '>%(levelname)-8s %(name)-12s %(funcName)-12s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging_level)
    other_isd_loggers = logging.getLogger('isdquantum.methods')
    other_isd_loggers.setLevel(logging_level)
    other_isd_loggers.addHandler(handler)
    other_isd_loggers = logging.getLogger('app')
    other_isd_loggers.setLevel(logging_level)
    other_isd_loggers.addHandler(handler)


def _get_sample_matrix_and_random_syndrome():
    ses = Session()

    logger.info("Trying to get isd parameters for {0}, {1}, {2}, {3}".format(
        ses.args.n, ses.args.k, ses.args.d, ses.args.w))
    h, _, syndromes, _, _, _ = rch.get_isd_systematic_parameters(
        ses.args.n, ses.args.k, ses.args.d, ses.args.w)
    ses.h = h
    ses.r = ses.args.n - ses.args.k
    syndrome = syndromes[randint(0, syndromes.shape[0] - 1)]
    ses.syndrome = syndrome


#     logger.debug("w = {0}; n = {1}; r = {2}".format(w, n, r))

#     logger.debug("Syndrome is {0}".format(syndrome))
