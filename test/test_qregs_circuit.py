import logging
from parameterized import parameterized
from isdquantum.utils import binary
from isdquantum.circuit import qregs_init as qregs
from test.common_circuit import CircuitTestCase
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import state_fidelity
import unittest


class QregsTestCase(CircuitTestCase):
    @parameterized.expand([
        ("10", 1),
        ("011", 1),
        ("1011", 1),
        ("1001", 1),
        ("1111", 1),
        ("101110", 1),
        ("1011010", 1),
        ("11001011", 1),
        ("110100000", 1),
        ("10", 2),
        ("110", 2),
        ("0011", 2),
        ("1011", 2),
        ("1001", 2),
        ("1111", 2),
        ("101110", 2),
        ("1011010", 2),
        ("11001011", 2),
        ("110100000", 2),
        ("10", 3),
        ("110", 3),
        ("0011", 3),
        ("1011", 3),
        ("1001", 3),
        ("1111", 3),
        ("101110", 3),
        ("1011010", 3),
        ("11001011", 3),
        ("110100000", 3),
    ])
    def test_conditionally_initialize_qureg_given_bitstring(
            self, name, num_controls):
        qubits = len(name)
        qr = QuantumRegister(qubits)
        qcontrols = QuantumRegister(num_controls)
        subsets = [tuple(range(i)) for i in range(num_controls + 1)]
        for subset in subsets:
            for mode in ['basic', 'advanced', 'noancilla']:
                with self.subTest(subset=subset, mode=mode):
                    self.logger.debug(
                        "Starting SUBTEST w/ subset {} and mode {}".format(
                            subset, mode))
                    qc = QuantumCircuit(qcontrols, qr)
                    if mode == 'basic':
                        if num_controls <= 2:
                            num_ancillae = 0
                        else:
                            num_ancillae = num_controls - 2
                    elif mode == 'noancilla':
                        num_ancillae = 0
                    else:
                        if num_controls <= 4:
                            num_ancillae = 0
                        else:
                            num_ancillae = 1
                    if num_ancillae > 0:
                        a = QuantumRegister(num_ancillae, name='a')
                        qc.add_register(a)
                    else:
                        a = None
                    for idx in subset:
                        qc.x(qcontrols[idx])
                    hasOps = qregs.conditionally_initialize_qureg_given_bitstring(
                        name, qr, qcontrols, a, qc, mode)

                    result = self.execute_statevector(qc)
                    vec = result.get_statevector()
                    exp_vec = [0] * (2**(qubits + num_ancillae + num_controls))
                    qcontrols_state = [0] * len(qcontrols)
                    for idx in subset:
                        qcontrols_state[idx] = 1
                    if (len(subset) == num_controls):
                        # All qcontrols enabled, i.e. all the num_controls positions of
                        # the state all 1, while all the previous positions are equal to
                        # bitstring
                        exp_state = [int(x) for x in name] + qcontrols_state
                    else:
                        exp_state = qcontrols_state[::-1]

                    exp_state_idx = binary.get_int_from_bitarray(exp_state)
                    exp_vec[exp_state_idx] = 1

                    f = state_fidelity(vec, exp_vec)
                    self.assertAlmostEqual(f, 1)

    @parameterized.expand([
        ("000"),
        ("100"),
        ("0011"),
        ("1011"),
        ("1001"),
        ("1111"),
        ("10110100"),
        ("11001011"),
        ("11010000"),
    ])
    def test_initialize_qureg_given_bitstring(self, name):
        qubits = len(name)
        qr = QuantumRegister(qubits)
        qc = QuantumCircuit(qr)
        hasOps = qregs.initialize_qureg_given_bitstring(name, qr, qc)
        if not hasOps:
            self.skipTest("No operation to perform given bitstring")
        result = self.execute_statevector(qc)
        vec = result.get_statevector()
        exp_vec = [0] * (2**qubits)
        exp_vec[binary.get_int_from_bitstring(name)] = 1
        f = state_fidelity(vec, exp_vec)
        self.assertAlmostEqual(f, 1)

    @parameterized.expand([
        ("000"),
        ("100"),
        ("0011"),
        ("1011"),
        ("1001"),
        ("1111"),
        ("10110100"),
        ("11001011"),
        ("11010000"),
    ])
    def test_initialize_qureg_given_bitarray(self, name):
        qubits = len(name)
        bitarray = [int(x) for x in name]
        qr = QuantumRegister(qubits)
        qc = QuantumCircuit(qr)
        hasOps = qregs.initialize_qureg_given_bitarray(bitarray, qr, qc)
        if not hasOps:
            self.skipTest("No operation to perform given bitstring")
        result = self.execute_statevector(qc)
        vec = result.get_statevector()
        exp_vec = [0] * (2**qubits)
        exp_vec[binary.get_int_from_bitstring(name)] = 1
        f = state_fidelity(vec, exp_vec)
        self.assertAlmostEqual(f, 1)

    @parameterized.expand([
        ("2", 2),
        ("3", 3),
        ("4", 4),
        ("5", 5),
        ("6", 6),
        ("7", 7),
        ("8", 8),
        ("9", 9),
        ("10", 10),
        ("11", 11),
        ("12", 12),
        ("13", 13),
        ("14", 14),
        ("15", 15),
        ("16", 16),
    ])
    def test_initialize_qureg_give_int(self, name, a_int):
        bits = binary.get_required_bits(a_int)
        qreg = QuantumRegister(bits)
        qc = QuantumCircuit(qreg)
        qregs.initialize_qureg_given_int(a_int, qreg, qc)
        vec = CircuitTestCase.execute_statevector(qc).get_statevector(qc)
        exp_vec = [0] * (2**bits)
        exp_vec[a_int] = 1
        # self.draw_circuit(qc, 'init_qreg_to_int_{}'.format(name))
        f = state_fidelity(vec, exp_vec)
        self.assertAlmostEqual(f, 1)

    @parameterized.expand([
        ("2", 2),
        ("3", 3),
        ("4", 4),
        ("5", 5),
        ("6", 6),
        ("7", 7),
        ("8", 8),
        ("9", 9),
        ("10", 10),
        ("11", 11),
        ("12", 12),
        ("13", 13),
        ("14", 14),
        ("15", 15),
        ("16", 16),
    ])
    def test_initialize_complemented_qureg_give_int(self, name, a_int):
        bits = binary.get_required_bits(a_int)
        qreg = QuantumRegister(bits)
        qc = QuantumCircuit(qreg)
        has_op = qregs.initialize_qureg_to_complement_of_int(a_int, qreg, qc)
        if (not has_op):
            self.skipTest("No operation to perform given bitstring")
        vec = CircuitTestCase.execute_statevector(qc).get_statevector(qc)
        exp_vec = [0] * (2**bits)
        neg_bs = binary.get_negated_bistring(
            binary.get_bitstring_from_int(a_int, bits))
        neg_i = binary.get_int_from_bitstring(neg_bs)
        exp_vec[neg_i] = 1
        f = state_fidelity(vec, exp_vec)
        self.assertAlmostEqual(f, 1)
