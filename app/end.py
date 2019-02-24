import logging
from app.session import Session
from isdquantum.utils import qiskit_support

logger = logging.getLogger(__name__)


def go():
    ses = Session()
    logger.info("H was\n{0}".format(ses.h))
    logger.info("Syndrome was\n{0}".format(ses.syndrome))
    logger.info("With {} accuracy error is \n{}".format(
        ses.alg_result.accuracy, ses.alg_result.error))
    if ses.args.export_qasm_file is not None:
        qiskit_support.export_circuit_to_qasm(ses.alg_result.qc,
                                              ses.args.export_qasm_file)
    if ses.args.draw_circuit:
        qiskit_support.draw_circuit(ses.alg_result.qc, ses.args.img_dir)
    if ses.args.draw_dag:
        qiskit_support.draw_dag(ses.alg_result.qc, ses.args.img_dir)
