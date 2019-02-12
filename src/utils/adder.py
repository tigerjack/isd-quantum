# -*- coding: utf-8 -*-

# Copyright 2017, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.
"""
Ripple adder example based on Cuccaro et al., quant-ph/0410184.
"""

import logging
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit

logger = logging.getLogger(__name__)


def _majority(p, a, b, c):
    """Majority gate."""
    p.cx(c, b)
    p.cx(c, a)
    p.ccx(a, b, c)


def _majority_i(p, a, b, c):
    p.ccx(a, b, c)
    p.cx(c, a)
    p.cx(c, b)


def _unmajority(p, a, b, c):
    """Unmajority gate."""
    p.ccx(a, b, c)
    p.cx(c, a)
    p.cx(a, b)


def _unmajority_i(p, a, b, c):
    p.cx(a, b)
    p.cx(c, a)
    p.ccx(a, b, c)


# Build a temporary subcircuit that adds a to b,
# storing the result in b
def adder_circuit(cin, a, b, cout):
    adder_subcircuit = QuantumCircuit(cin, a, b, cout)
    _majority(adder_subcircuit, cin[0], b[0], a[0])
    for j in range(a.size - 1):
        _majority(adder_subcircuit, a[j], b[j + 1], a[j + 1])
    adder_subcircuit.cx(a[a.size - 1], cout[0])
    for j in reversed(range(a.size - 1)):
        _unmajority(adder_subcircuit, a[j], b[j + 1], a[j + 1])
    _unmajority(adder_subcircuit, cin[0], b[0], a[0])
    return adder_subcircuit


def adder_circuit_i(cin, a, b, cout):
    adder_subcircuit = QuantumCircuit(cin, a, b, cout)
    _unmajority_i(adder_subcircuit, cin[0], b[0], a[0])
    for j in range(a.size - 1):
        _unmajority_i(adder_subcircuit, a[j], b[j + 1], a[j + 1])
    adder_subcircuit.cx(a[a.size - 1], cout[0])
    for j in reversed(range(a.size - 1)):
        _majority_i(adder_subcircuit, a[j], b[j + 1], a[j + 1])
    _majority_i(adder_subcircuit, cin[0], b[0], a[0])
    return adder_subcircuit
