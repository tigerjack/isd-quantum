import logging
from isdquantum.utils import binary
from qiskit.aqua import utils

logger = logging.getLogger(__name__)


#TODO comment codes
# Works also w/ array of ints
# a_str can be a string or a list
#TODO test cases
# TODO now they work w/ both list and string, maybe change names
def conditionally_initialize_qureg_given_bitarray(a_arr, qreg, qcontrols,
                                                  qancilla, circuit, mct_mode):
    """
    Given a binary array (i.e. a python list of 1's and 0's), initialize the qreg to the proper value corresponding to it if all the qcontrols qubits are set to 1. Basically, if a_arr is [1, 0, 1, 1], the qureg will be [1, 1, 0, 1], i.e. the function negate bits 3, 1 and 0 of the qreg.
    Note how the array is in fact reversed.

    :param a_arr: the binary array
    :param qreg: the QuantumRegister on which the integer should be set
    :param qcontrols: the control qubits
    :param qancilla: the ancilla qubits
    :param circuit: the QuantumCircuit containing all the previous qubits
    :param mct_mode: the QiskitAqua multi-control Toffoli mode
    :returns: False if no operation was performed, True if at least one operation was performed
    :rtype: bool

    """
    bits = len(a_arr)
    if (a_arr == [0] * bits):
        # Nothing to do, all zeros
        return False
    assert (len(qreg) >= len(a_arr)), "Not enough qubits for given bitstring"
    for i in reversed(range(bits)):
        if a_arr[i] == 1:
            if (qcontrols is None):
                logger.debug("x(a[{0}])".format(bits - i - 1))
                circuit.x(qreg[bits - i - 1])
            else:
                circuit.mct(
                    qcontrols, qreg[bits - i - 1], qancilla, mode=mct_mode)
        elif a_arr[i] != 0:
            raise Exception("binary string contains wrong value {0}".format(
                a_arr[i]))
    return True


def conditionally_initialize_qureg_given_bitstring(
        a_str, qreg, qcontrols, qancilla, circuit, mct_mode):
    """First converts the string into a list of ints and then run conditionally_initialize_qureg_given_bitarray (see)
    """
    a_list = [int(c) for c in a_str]
    return conditionally_initialize_qureg_given_bitarray(
        a_list, qreg, qcontrols, qancilla, circuit, mct_mode)


def conditionally_initialize_qureg_to_complement_of_bitstring(
        a_str, qreg, qcontrols, qancilla, circuit, mct_mode):
    """Initialize the qreg to the complement version of the string. I.e., if string is '1011', it initializes qreg to '0100'.
    """
    a_n_str = binary.get_negated_bistring(a_str)
    return conditionally_initialize_qureg_given_bitstring(
        a_n_str, qreg, qcontrols, qancilla, circuit, mct_mode)


def conditionally_initialize_qureg_to_complement_of_bitarray(
        a_str, qreg, qcontrols, qancilla, circuit, mct_mode):
    """Initialize the qreg to the complement version of the array. I.e., if array is [1, 0, 1, 1], it initializes qreg to [0, 1, 0, 0].
    """
    a_n_str = binary.get_negated_bitarray(a_str)
    return conditionally_initialize_qureg_given_bitarray(
        a_n_str, qreg, qcontrols, qancilla, circuit, mct_mode)


def initialize_qureg_given_bitstring(a_str, qreg, circuit):
    """
    Same as conditionally_initialize_qureg_given_bitarray but with no control qubits, i.e. the qubits are initialized no matter what
    """
    return conditionally_initialize_qureg_given_bitstring(
        a_str, qreg, None, None, circuit, None)


def initialize_qureg_given_bitarray(a_arr, qreg, circuit):
    """
    Same as conditionally_initialize_qureg_given_bitarray but with no control qubits, i.e. the qubits are initialized no matter what
    """
    return conditionally_initialize_qureg_given_bitarray(
        a_arr, qreg, None, None, circuit, None)


def initialize_qureg_to_complement_of_bitstring(a_str, qreg, circuit):
    """
    Initialize qureg to the complement of bitstring
    """
    a_n_str = binary.get_negated_bistring(a_str)
    return initialize_qureg_given_bitstring(a_n_str, qreg, circuit)


def initialize_qureg_to_complement_of_bitarray(a_arr, qreg, circuit):
    """
    Initialize qureg to the complement of bitarray
    """
    a_n_str = binary.get_negated_bitarray(a_arr)
    return initialize_qureg_given_bitstring(a_n_str, qreg, circuit)


def initialize_qureg_given_int(a_int, qreg, circuit):
    """
    Given a decimal integer, initialize the qreg to the proper value corresponding to it. Basically, if a_int is 11, i.e. 1011 in binary, the function negate bits 3, 1 and 0 of the qreg.
    Note that the qreg has the most significant bit in the rightmost part. In the circuit image, it means that the most significant bits are the lower ones of the qreg.

    Note also that if qreg has more qubits than the length of a_int in binary, only the first qubits are initialized. Continuing the previous example, if len(qreg) == 7, we still negate only bits 3, 1 and 0, while qubits from 4 on are untouched

    :param a_int: the integer in decimal base
    :param qreg: the QuantumRegister on which the integer should be set
    :param circuit: the QuantumCircuit containing the q_reg
    """
    a_str = binary.get_bitstring_from_int(a_int, len(qreg))
    return initialize_qureg_given_bitstring(a_str, qreg, circuit)


def initialize_qureg_to_complement_of_int(a_int, qreg, circuit):
    """
    Initialize qureg to the complement of int, see initialize_qureg_given_int.
    N.B. it's not the 2's complement, just a bitwise complement of all the bits of the binary representation of the int
    """
    a_str = binary.get_bitstring_from_int(a_int, len(qreg))
    return initialize_qureg_to_complement_of_bitstring(a_str, qreg, circuit)
