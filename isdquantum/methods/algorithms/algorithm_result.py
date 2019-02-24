import logging
_logger = logging.getLogger(__name__)


class AlgResult():
    def __init__(self, qc, error, accuracy, rounds, qiskit_result):
        "docstring"
        self.qc = qc
        self.error = error
        self.accuracy = accuracy
        self.rounds = rounds
        self.qiskit_result = qiskit_result
