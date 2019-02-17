import logging
from isdquantum.utils import binary
from isdquantum.utils import adder
from math import ceil, log

logger = logging.getLogger(__name__)


# Apply gates to the circuit to compute the hamming weight of a set of qubits.
# Return the list of qubits containing the result
# patterns_dict should be the result of the fpc_pattern
def get_circuit_for_qubits_weight(circuit, a_qs, cin_q, cout_qs,
                                  patterns_dict):
    assert len(a_qs) == patterns_dict['n_lines']
    assert len(cin_q) == 1
    assert len(cout_qs) == patterns_dict['n_couts']
    for i in patterns_dict['adders_pattern']:
        cout_idx = int(i[-1][1])
        half_bits = int((len(i) - 1) / 2)
        input_qubits = []
        for j in i:
            if j[0] == 'a':
                input_qubits.append(a_qs[int(j[1])])
            elif j[0] == 'c':
                input_qubits.append(cout_qs[int(j[1])])
            else:
                raise Exception("Invalid")
        logger.debug("{0}".format([input_qubits[i] for i in range(half_bits)]))
        logger.debug("{0}".format(
            [input_qubits[i] for i in range(half_bits, 2 * half_bits)]))
        logger.debug("{0}".format([cout_qs[cout_idx]]))
        adder.adder_circuit(
            circuit, cin_q, [input_qubits[i] for i in range(half_bits)],
            [input_qubits[i]
             for i in range(half_bits, 2 * half_bits)], [cout_qs[cout_idx]])
    to_measure_qubits = []
    for j in patterns_dict['results']:
        if j[0] == 'a':
            to_measure_qubits.append(a_qs[int(j[1])])
        elif j[0] == 'c':
            to_measure_qubits.append(cout_qs[int(j[1])])
        else:
            raise Exception("Invalid")
    return to_measure_qubits


def get_circuit_for_qubits_weight_i(circuit, a_qs, cin_q, cout_qs,
                                    patterns_dict):
    # patterns_dict = _fpc_pattern()
    # from qiskit import QuantumCircuit
    assert len(a_qs) == patterns_dict['n_lines']
    assert len(cin_q) == 1
    assert len(cout_qs) == patterns_dict['n_couts']
    for i in patterns_dict['adders_pattern'][::-1]:
        cout_idx = int(i[-1][1])
        half_bits = int((len(i) - 1) / 2)
        input_qubits = []
        for j in i:
            if j[0] == 'a':
                input_qubits.append(a_qs[int(j[1])])
            elif j[0] == 'c':
                input_qubits.append(cout_qs[int(j[1])])
            else:
                raise Exception("Invalid")
        logger.debug("{0}".format([input_qubits[i] for i in range(half_bits)]))
        logger.debug("{0}".format(
            [input_qubits[i] for i in range(half_bits, 2 * half_bits)]))
        logger.debug("{0}".format([cout_qs[cout_idx]]))
        adder.adder_circuit_i(
            circuit, cin_q, [input_qubits[i] for i in range(half_bits)],
            [input_qubits[i]
             for i in range(half_bits, 2 * half_bits)], [cout_qs[cout_idx]])


def get_circuit_for_qubits_weight_get_pattern(n):
    steps = ceil(log(n, 2))
    # TODO maybe we can use fewer lines
    # n_lines = n if n % 2 == 0 else n + 1
    n_lines = 2**steps
    patterns_dict = {}
    patterns_dict['n_lines'] = n_lines
    patterns_dict['n_couts'] = n_lines - 1
    # couts = list(reversed(range(patterns_dict['n_couts'])))
    couts = ["c{0}".format(i) for i in range(patterns_dict['n_couts'])][::-1]
    # inputs = [chr(c) for c in range(ord('a'), ord('h') + 1)][::-1]
    inputs = ["a{0}".format(i) for i in range(patterns_dict['n_lines'])][::-1]
    # inputs = list(range(patterns_dict['n_lines']))
    logger.debug("inputs {0}".format(inputs))
    logger.debug("couts {0}".format(couts))
    patterns_dict['adders_pattern'] = []

    n_adders = n_lines
    n_inputs_per_adders = 0
    inputs_next_stage = inputs
    for i in range(steps):
        n_adders = int(n_adders / 2)
        n_inputs_per_adders += 2
        outputs_this_stage = []
        logger.debug("Stage {0}, n_adder {1}, n_inputs_per_adder {2}".format(
            i, n_adders, n_inputs_per_adders))
        logger.debug("inputs_next_stage {0}".format(inputs_next_stage))
        for j in range(n_adders):
            logger.debug("Stage {0}, adder {1}".format(i, j))
            adder_inputs = []
            for k in range(n_inputs_per_adders):
                adder_inputs.append(inputs_next_stage.pop())
            adder_cout = couts.pop()
            adder_outputs = adder_inputs[int(len(adder_inputs) /
                                             2):len(adder_inputs)] + [
                                                 adder_cout
                                             ]
            patterns_dict['adders_pattern'].append(
                tuple(adder_inputs) + tuple([adder_cout]))
            logger.debug("{0}, {1} --> {2}".format(adder_inputs, adder_cout,
                                                   adder_outputs))
            outputs_this_stage += adder_outputs
        inputs_next_stage = outputs_this_stage[::-1]
    logger.debug("adders pattern\n{0}".format(patterns_dict['adders_pattern']))
    patterns_dict['results'] = inputs_next_stage[::-1]
    logger.debug("results\n{0}".format(patterns_dict['results']))
    return patterns_dict
