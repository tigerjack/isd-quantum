import logging
from parameterized import parameterized
from isdquantum.utils import adder
from test.common import BasicTestCase
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit import BasicAer, execute


class AdderTestCase(BasicTestCase):
    def _prepare_qubits(self, a_int, b_int):
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

    def _del_qubits(self):
        del self.a
        del self.b
        del self.cin
        del self.cout
        del self.ans
        del self.qc

    @parameterized.expand([
        ("3+2", 3, 2),
        ("7+9", 7, 9),
        ("15+11", 15, 11),
        ("15+1", 15, 1),
        ("24+7", 24, 7),
    ])
    def test_adder(self, name, a_int, b_int):
        self._prepare_qubits(a_int, b_int)
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
        self._del_qubits()

    @parameterized.expand([
        ("3+2", 3, 2),
        ("7+9", 7, 9),
        ("15+11", 15, 11),
        ("15+1", 15, 1),
        ("24+7", 24, 7),
    ])
    def test_adder_reverse(self, name, a_int, b_int):
        self._prepare_qubits(a_int, b_int)
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
        self._del_qubits()

    @parameterized.expand([
        ("5_on_4bits", 5, 4),
        ("5_on_3bits", 5, 3),
        ("7_on_3bits", 7, 3),
        ("7_on_5bits", 7, 5),
    ])
    def test_halves_sum(self, name, a_int, bits):
        if bits % 2 == 1:
            bits = bits + 1
        self.logger.debug("n bits = {0}".format(bits))
        half_bits = int(bits / 2)
        self.logger.debug("half bits = {0}".format(half_bits))
        a_str = bin(a_int)[2:].zfill(bits)
        self.logger.debug("a as string is {0}".format(a_str))

        a = QuantumRegister(bits, "a")
        cin = QuantumRegister(1, "cin")
        cout = QuantumRegister(1, "cout")
        ans = ClassicalRegister(half_bits + 1, "ans")
        qc = QuantumCircuit(a, cin, cout, ans)

        # Initialize a to its value
        for i in reversed(range(bits)):
            if (a_str[i] == '1'):
                self.logger.debug("x(a[{0}])".format(bits - i - 1))
                qc.x(a[bits - i - 1])

        adder.adder_circuit(qc, cin, [a[i] for i in range(half_bits)],
                            [a[i] for i in range(half_bits, bits)], cout)

        # Measure the output register in the computational basis
        for j in range(half_bits, bits):
            qc.measure(a[j], ans[j - half_bits])
        qc.measure(cout[0], ans[half_bits])

        counts = self.execute_qasm(qc)
        self.logger.debug("counts {0}".format(counts))
        a_half1_int = int(a_str[0:half_bits], 2)
        a_half2_int = int(a_str[half_bits:bits], 2)
        self.logger.debug("a first half = {0}".format(a_half1_int))
        self.logger.debug("a second half = {0}".format(a_half2_int))
        expected = bin(a_half1_int + a_half2_int)[2:].zfill(half_bits + 1)
        self.logger.debug(" '{0}': expected".format(expected))
        self.assertEqual(len(counts), 1)
        self.assertIn(expected, counts)
