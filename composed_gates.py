from qiskit import QuantumRegister
import logging
import pseudoquantumregister as pse


def n_controlled_n_target_gate(qc, control_register, target_register,
                               pseudo_ancilla_register, operation):
    single_control = n_control_compute(qc, control_register,
                                       pseudo_ancilla_register)
    # copy
    m = len(target_register)
    for i in range(m):
        operation(qc, single_control, target_register[i])
    # uncompute
    n_control_uncompute(qc, control_register, pseudo_ancilla_register)
    return single_control


# Given n controls qubit, w/ n > 1, returns the qubit usable for control
# and all the qubits added (as pseudo)
def n_control_compute(qc, control_register, pseudo_ancilla_register):
    n = len(control_register)
    _logger.debug(
        "n_control_compute -> {0} control qubits, needed {1} ancillas".format(
            n, n - 1))
    if (n <= 1):
        _logger.debug("Useless n control for single qubit")
        raise "Useless n control for single qubit"

    m = len(pseudo_ancilla_register)
    diff = m - (n - 1)
    _logger.debug(
        "n_control_compute -> ancilla registers alredy provided, size is {0}".
        format(pseudo_ancilla_register.size))
    if (diff < 0):
        _logger.debug(
            "Not enough ({0}) ancilla qubits for multi control w/ {1} qubits, needed {2}"
            .format(m, n, n - 1))
        pseudo_ancilla_register.add_up_to(qc, n - 1)
        _logger.debug(
            "Added the difference, now pseudo_ancilla_register is {0} size".
            format(len(pseudo_ancilla_register)))

    # compute
    qc.ccx(control_register[0], control_register[1],
           pseudo_ancilla_register[0])
    for i in range(2, n):
        qc.ccx(control_register[i], pseudo_ancilla_register[i - 2],
               pseudo_ancilla_register[i - 1])
    # pseudo_ancilla_register[n - 2] is the single control qubit
    return pseudo_ancilla_register[n - 2]


# This should be called just after the compute w/ the same control_register and
# also w/ the pseudo_ancilla_register returned from compute
def n_control_uncompute(qc, control_register, pseudo_ancilla_register):
    n = len(control_register)
    for i in range(n - 1, 1, -1):
        qc.ccx(control_register[i], pseudo_ancilla_register[i - 2],
               pseudo_ancilla_register[i - 1])
    qc.ccx(control_register[0], control_register[1],
           pseudo_ancilla_register[0])


_logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
_formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
_handler.setFormatter(_formatter)
if (_logger.hasHandlers()):
    _logger.handlers.clear()
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)
