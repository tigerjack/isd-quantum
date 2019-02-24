import logging
from isdquantum.methods.algorithms.lee_brickell_mixed_alg import LeeBrickellMixedAlg
from app.session import Session
from app import end
logger = logging.getLogger(__name__)


def go():
    ses = Session()
    lee = LeeBrickellMixedAlg(ses.h, ses.syndrome, ses.args.w, ses.args.p,
                              ses.need_measures, ses.args.mct_mode,
                              ses.args.nwr_mode)
    alg_result = lee.run(ses.args.provider, ses.args.backend)
    # ses.qc, ses.result, ses.error, ses.accuracy
    ses.alg_result = alg_result
    end.go()
