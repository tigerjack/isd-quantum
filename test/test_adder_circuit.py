import logging
import unittest
from parameterized import parameterized
from isdquantum.utils import adder
from test.common import BasicTestCase
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit import BasicAer, execute
from math import ceil, log


class AdderTestCase(BasicTestCase):
    @staticmethod
    def _check_adder_inputs(q_a, q_b, q_cin, q_cout):
        assert q_a.size == q_b.size, "The two adders must have the same size"
        assert q_cin.size == 1, "The carry-in register must have size 1"
        assert q_cout.size == 1, "The carry-out register must have size 1"

    @staticmethod
    def _check_enough_bits(a_int, bits):
        bits_required = ceil(log(a_int + 1, 2))
        assert bits >= bits_required, "Not enough bits."

    @staticmethod
    def _get_required_bits(*ints):
        if len(ints) == 0:
            raise Exception("ints greater than 0")
        if len(ints) == 1:
            bits = len("{0:b}".format(ints[0]))
        else:
            bits = len("{0:b}".format(max(ints)))
        return bits

    @staticmethod
    def _get_bitstring_from_int(i, max_bits):
        str = bin(i)[2:].zfill(max_bits)
        if len(str) > max_bits:
            raise Exception("more than max_bits")
        return str

    @staticmethod
    def _get_int_from_bitstring(a_str):
        return int(a_str, 2)

    @staticmethod
    def _initialize_qureg_given_int(a_int, q_reg, circuit, bits):
        a_str = AdderTestCase._get_bitstring_from_int(a_int, bits)
        bits = len(a_str)
        for i in reversed(range(bits)):
            if (a_str[i] == '1'):
                AdderTestCase.logger.debug("x(a[{0}])".format(bits - i - 1))
                circuit.x(q_reg[bits - i - 1])

    def _prepare_adder_circuit(self, bits):
        self.a = QuantumRegister(bits, "a")
        self.b = QuantumRegister(bits, "b")
        self.cin = QuantumRegister(1, "cin")
        self.cout = QuantumRegister(1, "cout")
        self.qc = QuantumCircuit(self.a, self.b, self.cin, self.cout)
        self.clean = False

    def _del_qubits(self):
        del self.a
        del self.b
        del self.cin
        del self.cout
        del self.qc
        self.clean = True

    def setUp(self):
        self.clean = True

    def tearDown(self):
        self.assertTrue(self.clean)

    @parameterized.expand([
        ("3+2", 3, 2),
        ("7+9", 7, 9),
        ("15+11", 15, 11),
        ("15+1", 15, 1),
        ("24+7", 24, 7),
    ])
    # @unittest.skip("No reason")
    def test_adder(self, name, a_int, b_int):
        bits = self._get_required_bits(a_int, b_int)
        self._prepare_adder_circuit(bits)
        self._check_adder_inputs(self.a, self.b, self.cin, self.cout)

        self._initialize_qureg_given_int(a_int, self.a, self.qc, bits)
        self._initialize_qureg_given_int(b_int, self.b, self.qc, bits)

        # Apply the adder
        adder.adder_circuit(self.qc, self.cin, self.a, self.b, self.cout)

        # Measure the output register in the computational basis
        ans = ClassicalRegister(self.b.size + self.cout.size, "ans")
        self.qc.add_register(ans)
        for j in range(self.b.size):
            self.qc.measure(self.b[j], ans[j])
        self.qc.measure(self.cout[0], ans[self.b.size])

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
    # @unittest.skip("No reason")
    def test_adder_inverse(self, name, a_int, b_int):
        bits = self._get_required_bits(a_int, b_int)
        self._prepare_adder_circuit(bits)
        self._check_adder_inputs(self.a, self.b, self.cin, self.cout)

        self._initialize_qureg_given_int(a_int, self.a, self.qc, bits)
        self._initialize_qureg_given_int(b_int, self.b, self.qc, bits)
        adder.adder_circuit(self.qc, self.cin, self.a, self.b, self.cout)
        adder.adder_circuit_i(self.qc, self.cin, self.a, self.b, self.cout)

        # Measure results
        ans = ClassicalRegister(self.b.size + self.cout.size, "ans")
        self.qc.add_register(ans)
        for j in range(self.b.size):
            self.qc.measure(self.b[j], ans[j])
        self.qc.measure(self.cout[0], ans[self.b.size])

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
    # @unittest.skip("No reason")
    def test_halves_sum(self, name, a_int, bits):
        if bits % 2 == 1:
            bits = bits + 1
        self.logger.debug("n bits = {0}".format(bits))
        self._check_enough_bits(a_int, bits)
        half_bits = int(bits / 2)
        self.logger.debug("half bits = {0}".format(half_bits))

        self._prepare_adder_circuit(bits)

        # Initialize a to its value
        self._initialize_qureg_given_int(a_int, self.a, self.qc, bits)

        adder.adder_circuit(
            self.qc, self.cin, [self.a[i] for i in range(half_bits)],
            [self.a[i] for i in range(half_bits, bits)], self.cout)

        # Measure the output register in the computational basis
        ans = ClassicalRegister(half_bits + self.cout.size, "ans")
        self.qc.add_register(ans)
        for j in range(half_bits, bits):
            self.qc.measure(self.a[j], ans[j - half_bits])
        self.qc.measure(self.cout[0], ans[half_bits])

        counts = self.execute_qasm(self.qc)
        self.logger.debug("counts {0}".format(counts))
        a_str = self._get_bitstring_from_int(a_int, bits)
        a_half1_int = self._get_int_from_bitstring(a_str[0:half_bits])
        a_half2_int = self._get_int_from_bitstring(a_str[half_bits:bits])
        # a_half1_int = int(a_str[0:half_bits], 2)
        # a_half2_int = int(a_str[half_bits:bits], 2)
        self.logger.debug("a first half = {0}".format(a_half1_int))
        self.logger.debug("a second half = {0}".format(a_half2_int))
        expected = self._get_bitstring_from_int(a_half1_int + a_half2_int,
                                                half_bits + 1)
        self.logger.debug(" '{0}': expected".format(expected))
        self.assertEqual(len(counts), 1)
        self.assertIn(expected, counts)
        self._del_qubits()

    @parameterized.expand([
        ("1_on_4", 1, 4),
        ("2_on_4", 2, 4),
        ("3_on_4", 3, 4),
        ("4_on_4", 4, 4),
        ("5_on_4", 5, 4),
        ("6_on_4", 6, 4),
        ("7_on_4", 7, 4),
        ("8_on_5", 8, 5),
        ("9_on_5", 9, 5),
        ("10_on_5", 10, 5),
        ("11_on_5", 11, 5),
        ("12_on_5", 12, 5),
    ])
    # @unittest.skip("No reason")
    def test_weight_equals_w_hadamards(self, name, eq_int, bits):
        ### Prepare qubits
        ######
        if bits % 2 == 1:
            bits = bits + 1
        half_bits = int(bits / 2)
        self._check_enough_bits(eq_int, half_bits + 1)
        equal_str = bin(eq_int)[2:].zfill(half_bits + 1)
        self.logger.debug("equal_str = {0}".format(equal_str))

        a = QuantumRegister(half_bits, "a")
        b = QuantumRegister(half_bits, "b")
        cin = QuantumRegister(1, "cin")
        cout = QuantumRegister(1, "cout")
        eq = QuantumRegister(1, 'eq')
        anc = QuantumRegister(1, 'anc')
        # Have to measure a, b and eq
        ans = ClassicalRegister(a.size + b.size + eq.size, "ans")
        qc = QuantumCircuit(a, b, cin, cout, eq, anc, ans)

        # Assert
        self._check_adder_inputs(a, b, cin, cout)
        self.assertEqual(ans.size, a.size + b.size + eq.size)

        # Hadamards all qubits
        qc.h(a)
        qc.h(b)
        # Apply the adder
        adder.adder_circuit(qc, cin, a, b, cout)
        qc.barrier()

        # Add the negated equal_str to {b, cout}.
        if equal_str[0] == '0':
            self.logger.debug("x(cout[0])")
            qc.x(cout[0])
        for i in range(1, len(equal_str)):
            if (equal_str[i] == '0'):
                self.logger.debug("x(b[{0}])".format(half_bits - i))
                qc.x(b[half_bits - i])
        qc.barrier()

        # If output is 11..1, set eq to 1
        qc.mct(
            [qb for qb in b] + [qcout for qcout in cout],
            eq[0],
            anc,
            mode='advanced')
        qc.barrier()

        # Restore b
        if equal_str[0] == '0':
            self.logger.debug("x(cout[0])")
            qc.x(cout[0])
        for i in range(1, len(equal_str)):
            if (equal_str[i] == '0'):
                self.logger.debug("x(b[{0}])".format(half_bits - i))
                qc.x(b[half_bits - i])
        qc.barrier()
        adder.adder_circuit_i(qc, cin, a, b, cout)

        for i, qr in enumerate(chain(a, b, eq)):
            qc.measure(qr, ans[i])

        ###############################################################
        # execute the program on qasm
        ###############################################################
        counts = BasicTestCase.execute_qasm(qc)
        # self.logger.debug(counts)
        for i in counts.keys():
            if i[0] == '1':
                self.logger.debug("Eq active, state is {0}".format(i))
                a_int = self._get_int_from_bitstring(i[1:half_bits + 1])
                b_int = self._get_int_from_bitstring(i[half_bits + 1:bits + 1])
                self.assertEqual(a_int + b_int, eq_int)

        if self.draw:
            BasicTestCase.draw_circuit(
                qc, 'data/img/adder_w_hadamards_{0}.png'.format(name))
