import logging
from isdquantum.utils import hamming_weight_compute as hwc
from isdquantum.utils import adder
from isdquantum.utils import binary
from isdquantum.utils import qregs
from test.common_circuit import CircuitTestCase
from math import factorial
from parameterized import parameterized
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit.aqua import utils


class PopulationCountTestCase(CircuitTestCase):
    @parameterized.expand([
        ("0000"),
        ("0101"),
        ("0001"),
        ("1101"),
        ("1001"),
        ("1111"),
        ("10110100"),
        ("11001011"),
        ("11010000"),
    ])
    def test_fast_population_count(self, name):
        nwr_dict = hwc.get_circuit_for_qubits_weight_get_pattern(len(name))
        result_bit_length = len(nwr_dict['results'])
        a = QuantumRegister(nwr_dict['n_lines'], 'a')
        cin = QuantumRegister(1, 'cin')
        cout = QuantumRegister(nwr_dict['n_couts'], 'cout')
        cr = ClassicalRegister(len(nwr_dict['results']))
        qc = QuantumCircuit(cin, a, cout, cr, name='test_fpt_{0}'.format(name))

        _ = qregs.initialize_qureg_given_bitstring(name, a, qc)

        to_measure_qubits = hwc.get_circuit_for_qubits_weight(
            qc, a, cin, cout, nwr_dict)

        for i, qb in enumerate(to_measure_qubits):
            qc.measure(qb, cr[i])

        counts = CircuitTestCase.execute_qasm(qc)
        self.logger.info(counts)
        exp_w = name.count("1")
        exp_w_bitstring = binary.get_bitstring_from_int(
            exp_w, result_bit_length)
        self.assertEqual(len(counts), 1)
        self.assertIn(exp_w_bitstring, counts)

    @parameterized.expand([
        ("0000"),
        ("0101"),
        ("0001"),
        ("1101"),
        ("1001"),
        ("1111"),
        ("10110100"),
        ("11001011"),
        ("11010000"),
    ])
    def test_fast_population_count_i(self, name):
        nwr_dict = hwc.get_circuit_for_qubits_weight_get_pattern(len(name))
        result_bit_length = len(nwr_dict['results'])
        a = QuantumRegister(nwr_dict['n_lines'], 'a')
        cin = QuantumRegister(1, 'cin')
        cout = QuantumRegister(nwr_dict['n_couts'], 'cout')
        cr = ClassicalRegister(len(a))
        qc = QuantumCircuit(cin, a, cout, cr, name='test_fpt_{0}'.format(name))

        _ = qregs.initialize_qureg_given_bitstring(name, a, qc)
        to_measure_qubits = hwc.get_circuit_for_qubits_weight(
            qc, a, cin, cout, nwr_dict)
        hwc.get_circuit_for_qubits_weight_i(qc, a, cin, cout, nwr_dict)

        qc.measure(a, cr)

        counts = CircuitTestCase.execute_qasm(qc)
        self.logger.debug(counts)
        self.assertEqual(len(counts), 1)
        self.assertIn(name, counts)

    @parameterized.expand([
        ("0000"),
        ("0101"),
        ("0001"),
        ("1101"),
        ("1001"),
        ("1111"),
        ("10110100"),
        ("11001011"),
        ("11010000"),
    ])
    def test_fast_population_count_full_i(self, name):
        nwr_dict = hwc.get_circuit_for_qubits_weight_get_pattern(len(name))
        result_bit_length = len(nwr_dict['results'])
        a = QuantumRegister(nwr_dict['n_lines'], 'a')
        cin = QuantumRegister(1, 'cin')
        cout = QuantumRegister(nwr_dict['n_couts'], 'cout')
        cr = ClassicalRegister(len(a))
        qc = QuantumCircuit(cin, a, cout, cr, name='test_fpt_{0}'.format(name))

        _ = qregs.initialize_qureg_given_bitstring(name, a, qc)
        to_measure_qubits = hwc.get_circuit_for_qubits_weight(
            qc, a, cin, cout, nwr_dict)
        hwc.get_circuit_for_qubits_weight_i(qc, a, cin, cout, nwr_dict)
        _ = qregs.initialize_qureg_given_bitstring(name, a, qc)

        qc.measure(a, cr)

        counts = CircuitTestCase.execute_qasm(qc)
        self.logger.debug(counts)
        self.assertEqual(len(counts), 1)
        self.assertIn('0' * len(cr), counts)

    @parameterized.expand([
        (("2on4"), 2, 4),
        (("3on4"), 3, 4),
        (("3on8"), 1, 8),
        (("3on8"), 2, 8),
        (("3on8"), 3, 8),
        (("3on8"), 4, 8),
    ])
    def test_fast_population_count_w_hadamards(self, name, weight_int, n_bits):
        nwr_dict = hwc.get_circuit_for_qubits_weight_get_pattern(n_bits)
        result_bit_length = len(nwr_dict['results'])
        a = QuantumRegister(nwr_dict['n_lines'], 'a')
        cin = QuantumRegister(1, 'cin')
        cout = QuantumRegister(nwr_dict['n_couts'], 'cout')
        qc = QuantumCircuit(cin, a, cout, name='test_fpt_{0}'.format(name))

        eq = QuantumRegister(1, 'eq')
        anc = QuantumRegister(1, 'anc')

        # Have to measure a and eq
        cr = ClassicalRegister(a.size + eq.size, "ans")
        qc.add_register(eq, anc, cr)

        qc.h(a)
        result_qubits = hwc.get_circuit_for_qubits_weight_check(
            qc, a, cin, cout, eq, anc, weight_int, nwr_dict)
        hwc.get_circuit_for_qubits_weight_check_i(
            qc,
            a,
            cin,
            cout,
            eq,
            anc,
            weight_int,
            nwr_dict,
            result_qubits,
            uncomputeEq=False)

        qc.measure([aq for aq in a] + [eq[0]], cr)

        # QASM
        counts = CircuitTestCase.execute_qasm(qc, 2048)
        self.logger.debug(counts)
        total_actives = 0
        for i in counts.keys():
            if i[0] == '1':
                total_actives += 1
                self.logger.debug("Eq active, full state is {0}".format(i))
                self.assertEqual(i[1:].count('1'), weight_int)
        exp_actives = factorial(n_bits) / factorial(weight_int) / factorial(
            n_bits - weight_int)
        self.assertEqual(total_actives, exp_actives)
