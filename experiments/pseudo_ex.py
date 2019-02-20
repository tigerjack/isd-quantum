import os
import sys
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import pseudoquantumregister as pse

from qiskit import QuantumRegister, QuantumCircuit


def test0():
    a = QuantumRegister(3)
    b = QuantumRegister(5)
    c = pse.PseudoQuantumRegister('test0')
    c.add_registers(a, b)
    assert c.size == 8


def test_cnots():
    a = QuantumRegister(3, 'a')
    b = QuantumRegister(5, 'b')
    qc = QuantumCircuit(a, b)
    c = pse.PseudoQuantumRegister('test0')
    c.add_registers(a, b)

    qc.ccx(c[0], c[1], c[2])
    qc.ccx(c[2], c[3], c[4])
    from qiskit.tools.visualization import circuit_drawer
    circuit_drawer(qc, filename="../img/pseudo_test.png")


def main():
    test0()
    test_cnots()


if __name__ == "__main__":
    main()
