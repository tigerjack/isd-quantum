import logging
from parameterized import parameterized
from src.utils import adder
from test.common import BasicTestCase
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit import BasicAer, execute


class AdderTestCase(BasicTestCase):
    def prepare_qubits(self, a_int, b_int):
        bits = len("{0:b}".format(max(a_int, b_int)))
        a_str = bin(a_int)[2:].zfill(bits)
        b_str = bin(b_int)[2:].zfill(bits)

        self.a = QuantumRegister(bits, "a")
        self.b = QuantumRegister(bits, "b")
        self.cin = QuantumRegister(1, "cin")
        self.cout = QuantumRegister(1, "cout")
        self.ans = ClassicalRegister(bits + 1, "ans")
        self.qc = QuantumCircuit(self.a, self.b, self.cin, self.cout, self.ans)

        for i in reversed(range(bits)):
            if (a_str[i] == '1'):
                self.logger.debug("x(a[{0}])".format(bits - i - 1))
                self.qc.x(self.a[bits - i - 1])
            if (b_str[i] == '1'):
                self.logger.debug("x(b[{0}])".format(bits - i - 1))
                self.qc.x(self.b[bits - i - 1])

    @parameterized.expand([
        ("3+2", 3, 2),
        ("7+9", 7, 9),
        ("15+11", 15, 11),
        ("15+1", 15, 1),
        ("24+7", 24, 7),
    ])
    def test_adder(self, name, a_int, b_int):
        self.prepare_qubits(a_int, b_int)
        self.assertEqual(self.a.size, self.b.size)
        self.assertEqual(self.cin.size, 1)
        self.assertEqual(self.cout.size, 1)
        self.assertEqual(self.ans.size, self.a.size + 1)
        # Apply the adder
        adder.adder_circuit(self.qc, self.cin, self.a, self.b, self.cout)

        # Measure the output register in the computational basis
        for j in range(self.b.size):
            self.qc.measure(self.b[j], self.ans[j])
        self.qc.measure(self.cout[0], self.ans[self.b.size])

        ###############################################################
        # execute the program on qasm
        ###############################################################
        counts = BasicTestCase.execute_qasm(self.qc)
        expected = bin(a_int + b_int)[2:].zfill(self.a.size + 1)
        self.assertEqual(len(counts), 1)
        self.assertIn(expected, counts)

    @parameterized.expand([
        ("3+2", 3, 2),
        ("7+9", 7, 9),
        ("15+11", 15, 11),
        ("15+1", 15, 1),
        ("24+7", 24, 7),
    ])
    def test_adder_reverse(self, name, a_int, b_int):
        self.prepare_qubits(a_int, b_int)
        self.assertEqual(self.a.size, self.b.size)
        self.assertEqual(self.cin.size, 1)
        self.assertEqual(self.cout.size, 1)
        self.assertEqual(self.ans.size, self.a.size + 1)
        adder.adder_circuit(self.qc, self.cin, self.a, self.b, self.cout)
        adder.adder_circuit_i(self.qc, self.cin, self.a, self.b, self.cout)
        for j in range(self.b.size):
            self.qc.measure(self.b[j], self.ans[j])
        self.qc.measure(self.cout[0], self.ans[self.b.size])

        ###############################################################
        # execute the program on qasm
        ###############################################################
        counts = BasicTestCase.execute_qasm(self.qc)
        expected = bin(b_int)[2:].zfill(self.a.size + 1)
        self.assertEqual(len(counts), 1)
        self.assertIn(expected, counts)
