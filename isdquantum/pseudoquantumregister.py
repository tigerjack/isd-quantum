from qiskit import QuantumRegister, QuantumCircuit


class PseudoQuantumRegister():
    def __init__(self, name=None):
        self.registers = []
        self.name = name
        self.size = 0

    def add_registers(self, *quantum_registers):
        for quantum_register in quantum_registers:
            if not isinstance(quantum_register, QuantumRegister):
                raise TypeError("expected quantum register")
            for qubit in quantum_register:
                self.registers.append(qubit)
                self.size += 1

    def add_qubits(self, *qubits):
        for qubit in qubits:
            # TODO this is just a workaround to check if it's a qubit,
            # but better method should exists
            if not isinstance(qubit, tuple) or not (isinstance(
                    qubit[0], QuantumRegister)):
                raise TypeError("expected qubit")
            self.registers.append(qubit)
            self.size += 1

    # If registers contains m qubits, w/ m < n, add the remaining n - m qubits
    def add_up_to(self, qc, n):
        diff = n - self.size
        if diff > 0:
            tmp = QuantumRegister(diff)
            qc.add_register(tmp)
            self.add_registers(tmp)

    def print_registers(self):
        for register in self.registers:
            print(register)

    def check_range(self, j):
        """Check that j is a valid index into self."""
        if j < 0 or j >= self.size:
            raise IndexError("register index out of range")

    def __len__(self):
        """Return register size"""
        return self.size

    def __getitem__(self, key):
        """
        Arg:
            key (int): index of the bit/qubit to be retrieved.

        Returns:
            tuple[Register, int]: a tuple in the form `(self, key)`.

        Raises:
            QiskitError: if the `key` is not an integer.
            QiskitIndexError: if the `key` is not in the range
                `(0, self.size)`.
        """
        if not isinstance(key, int):
            raise TypeError("expected integer index into register")
        self.check_range(key)
        return self.registers[key]
