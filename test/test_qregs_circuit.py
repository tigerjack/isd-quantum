import logging
from parameterized import parameterized
from isdquantum.utils import binary
from isdquantum.utils import qregs
from test.common_circuit import CircuitTestCase
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import state_fidelity


class QregsTestCase(CircuitTestCase):
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
        vec = CircuitTestCase.execute_statevector(qc)
        exp_vec = [0] * (2**bits)
        exp_vec[a_int] = 1
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
        vec = CircuitTestCase.execute_statevector(qc)
        exp_vec = [0] * (2**bits)
        neg_bs = binary.get_negated_bistring(
            binary.get_bitstring_from_int(a_int, bits))
        neg_i = binary.get_int_from_bitstring(neg_bs)
        exp_vec[neg_i] = 1
        f = state_fidelity(vec, exp_vec)
        self.assertAlmostEqual(f, 1)
