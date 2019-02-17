import logging
from isdquantum.utils import binary
from qiskit.aqua import utils

logger = logging.getLogger(__name__)

#TODO comment codes


# Works w/ array also
# a_str can be a string or a list
#TODO test cases
def conditionally_initialize_qureg_given_bitstring(
        a_str, qreg, qcontrols, qancilla, circuit, mct_mode):
    if isinstance(a_str, str):
        a_list = [int(c) for c in a_str]
    elif isinstance(a_str, list):
        a_list = a_str
    else:
        raise Exception("Unrecognized format, must be a string or a list")
    bits = len(a_str)
    if (a_list == [0] * bits):
        # Nothing to do, all zeros
        return False
    assert (len(qreg) >= len(a_list)), "Not enough qubits for given bitstring"
    for i in reversed(range(bits)):
        if a_list[i] == 1:
            if (qcontrols is None):
                logger.debug("x(a[{0}])".format(bits - i - 1))
                circuit.x(qreg[bits - i - 1])
            else:
                circuit.mct(
                    qcontrols, qreg[bits - i - 1], qancilla, mode=mct_mode)
        elif a_list[i] != 0:
            raise Exception("binary string contains wrong value {0}".format(
                a_list[i]))
    return True


def initialize_qureg_given_bitstring(a_str, qreg, circuit):
    """
    Given a binary string, initialize the qreg to the proper value
    corresponding to it. Basically, if a_str is 1011,
    the function negate bits 0, 1 and 3 of the qreg.
    # 3->0; 2->1; 1->2; 0;3
    Note that the qreg has the most significant bit in the rightmost part (little endian)
    of the qreg, i.e. the most significant bit is on qreg 0.
    In the circuit, it means that the most significant bits are the lower ones of the qreg

    :param a_str: the binary digits bit string
    :param qreg: the QuantumRegister on which the integer should be set
    :param circuit: the QuantumCircuit containing the q_reg

    :return False if no operation was performed, True if at least one operation was performed
    """
    return conditionally_initialize_qureg_given_bitstring(
        a_str, qreg, None, None, circuit, None)


def initialize_qureg_given_int(a_int, qreg, circuit):
    """
    Given a decimal integer, initialize the qreg to the proper value
    corresponding to it. Basically, if a_int is 11, i.e. 1011 in binary,
    the function negate bits 3, 2 and 0 of the qreg. Note that the qreg has the
    most significant bit in the leftmost part (big endian)

    :param a_int: the integer in decimal base
    :param qreg: the QuantumRegister on which the integer should be set
    :param circuit: the QuantumCircuit containing the q_reg
    """
    a_str = binary.get_bitstring_from_int(a_int, len(qreg))
    return initialize_qureg_given_bitstring(a_str, qreg, circuit)


# I.e. if bitstring is 1011, it initializes the qreg to 0100
def initialize_qureg_to_complement_of_bitstring(a_str, qreg, circuit):
    a_n_str = binary.get_negated_bistring(a_str)
    return initialize_qureg_given_bitstring(a_n_str, qreg, circuit)


def initialize_qureg_to_complement_of_int(a_int, qreg, circuit):
    a_str = binary.get_bitstring_from_int(a_int, len(qreg))
    return initialize_qureg_to_complement_of_bitstring(a_str, qreg, circuit)
