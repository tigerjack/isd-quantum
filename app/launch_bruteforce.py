import logging
from isdquantum.methods.algorithms.bruteforce_alg import BruteforceAlg
from isdquantum.utils import qiskit_support
from app.session import Session
from app import end
logger = logging.getLogger(__name__)


def go():
    ses = Session()
    bru = BruteforceAlg(ses.h, ses.syndrome, ses.args.w, ses.need_measures,
                        ses.args.mct_mode, ses.args.nwr_mode)
    ses.qc, ses.backend, rounds = bru.prepare_circuit_for_backend(
        ses.args.provider, ses.args.backend)
    if ses.args.infos:
        infos = qiskit_support.get_compiled_circuit_infos(ses.qc, ses.backend)
        for k, v in infos.items():
            print("{} --> {}".format(k, v))
    if ses.args.export_qasm_file is not None:
        qiskit_support.export_circuit_to_qasm(ses.qc,
                                              ses.args.export_qasm_file)

    if (ses.args.not_execute):
        logger.debug("Not execute set to true, exiting.")
        end.go()
    alg_result = bru.run_circuit_on_backend(ses.qc, ses.backend)
    alg_result.rounds = rounds
    ses.alg_result = alg_result
    # ses.result, ses.error, ses.accuracy
    end.go()
