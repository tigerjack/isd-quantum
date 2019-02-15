import logging
from isdquantum.utils import binary

logger = logging.getLogger(__name__)


def initialize_qureg_given_bitstring(a_str, qreg, circuit):
    """
    Given a binary string, initialize the qreg to the proper value
    corresponding to it. Basically, if a_str is 1011,
    the function negate bits 3, 2 and 0 of the qreg.
    Note that the qreg has the most significant bit in the leftmost part (big endian)

    :param a_str: the binary digits bit string
    :param qreg: the QuantumRegister on which the integer should be set
    :param circuit: the QuantumCircuit containing the q_reg

    :return False if no operation was performed, True if at least one operation was performed
    """
    bits = len(a_str)
    if (a_str == '0' * bits):
        # Nothing to do, all zeros
        return False
    assert (len(qreg) >= len(a_str))
    for i in reversed(range(bits)):
        if (a_str[i] == '1'):
            logger.debug("x(a[{0}])".format(bits - i - 1))
            circuit.x(qreg[bits - i - 1])
        elif (a_str[i] != '0'):
            raise Exception("binary string contains wrong values")
    return True


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
