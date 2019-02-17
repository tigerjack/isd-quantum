import logging
from math import ceil, log

logger = logging.getLogger(__name__)


def check_enough_bits(a_int, bits):
    bits_required = get_required_bits(a_int)
    assert bits >= bits_required, "Not enough bits."


def get_required_bits(*ints):
    if len(ints) == 0:
        raise Exception("number of ints must be greater than 0")
    if len(ints) == 1:
        to_check_int = ints[0]
    else:
        to_check_int = max(ints)
    if to_check_int < 0:
        to_check_int = -to_check_int
    bits_required = ceil(log(to_check_int + 1, 2))
    return bits_required


# WARN: Returns 2's complement. If you want the negation of the bitstring
# representing i, you can use this method followed by the get_negated_bitstring
def get_bitstring_from_int(i, max_bits, littleEndian=False):
    if i >= 0:
        str = bin(i)[2:].zfill(max_bits)
    else:
        str = bin(2**max_bits + i)[2:].zfill(max_bits)
    if len(str) > max_bits:
        raise Exception("more than max_bits")
    return str if not littleEndian else str[::-1]


def get_negated_bistring(a_str):
    return a_str.translate(str.maketrans('01', '10'))


def get_int_from_bitstring(a_str, littleEndian=False):
    return int(a_str if not littleEndian else a_str[::-1], 2)
