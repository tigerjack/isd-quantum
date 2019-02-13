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


def _majority(circuit, a, b, c):
    """Majority gate."""
    circuit.cx(c, b)
    circuit.cx(c, a)
    circuit.ccx(a, b, c)


def _majority_i(circuit, a, b, c):
    circuit.ccx(a, b, c)
    circuit.cx(c, a)
    circuit.cx(c, b)


def _unmajority(circuit, a, b, c):
    """Unmajority gate."""
    circuit.ccx(a, b, c)
    circuit.cx(c, a)
    circuit.cx(a, b)


def _unmajority_i(circuit, a, b, c):
    circuit.cx(a, b)
    circuit.cx(c, a)
    circuit.ccx(a, b, c)


# Build a temporary subcircuit that adds a to b,
# storing the result in b
def adder_circuit(circuit, cin, a, b, cout):
    # adder_subcircuit = QuantumCircuit(cin, a, b, cout)
    _majority(circuit, cin[0], b[0], a[0])
    for j in range(len(a) - 1):
        _majority(circuit, a[j], b[j + 1], a[j + 1])
    circuit.cx(a[len(a) - 1], cout[0])
    for j in reversed(range(len(a) - 1)):
        _unmajority(circuit, a[j], b[j + 1], a[j + 1])
    _unmajority(circuit, cin[0], b[0], a[0])


def adder_circuit_i(circuit, cin, a, b, cout):
    # adder_subcircuit = QuantumCircuit(cin, a, b, cout)
    _unmajority_i(circuit, cin[0], b[0], a[0])
    for j in range(len(a) - 1):
        _unmajority_i(circuit, a[j], b[j + 1], a[j + 1])
    circuit.cx(a[len(a) - 1], cout[0])
    for j in reversed(range(len(a) - 1)):
        _majority_i(circuit, a[j], b[j + 1], a[j + 1])
    _majority_i(circuit, cin[0], b[0], a[0])
