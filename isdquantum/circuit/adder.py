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


# Build a temporary subcircuit that adds a to b,
# storing the result in b
def adder_circuit(circuit, cin, a, b, cout):
    _check_adder_inputs(a, b, cin, cout)
    _majority(circuit, cin[0], b[0], a[0])
    for j in range(len(a) - 1):
        _majority(circuit, a[j], b[j + 1], a[j + 1])
    circuit.cx(a[len(a) - 1], cout[0])
    for j in reversed(range(len(a) - 1)):
        _unmajority(circuit, a[j], b[j + 1], a[j + 1])
    _unmajority(circuit, cin[0], b[0], a[0])


def adder_circuit_i(circuit, cin, a, b, cout):
    _check_adder_inputs(a, b, cin, cout)
    _unmajority_i(circuit, cin[0], b[0], a[0])
    for j in range(len(a) - 1):
        _unmajority_i(circuit, a[j], b[j + 1], a[j + 1])
    circuit.cx(a[len(a) - 1], cout[0])
    for j in reversed(range(len(a) - 1)):
        _majority_i(circuit, a[j], b[j + 1], a[j + 1])
    _majority_i(circuit, cin[0], b[0], a[0])


def _check_adder_inputs(q_a, q_b, q_cin, q_cout):
    assert len(q_a) == len(q_b), "The two adders must have the same size"
    assert len(q_cin) >= 1, "The carry-in register must have size least 1"
    assert len(q_cout) >= 1, "The carry-out register must have size at least 1"


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
