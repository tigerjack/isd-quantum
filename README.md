# isd-quantum

Quantum circuits implemented in `Qiskit` to solve the Information Set Decoding problem using Grover's algorithm.
At the moment, an exhaustive search and a variant of Lee-Brickell's algorithm are proposed.

All the latest code is in `testing` branch. Tests are based on some of the https://github.com/tigerjack/isd-classic hardcoded matrixes. 

Test cases give an idea of the main usage of both circuits and the whole algorithms. The most recent test cases are the `*statevector` ones, the other still needs double-checks.

Circuits are under `isdquantum.methods.circuits`, while support circuits under `isdquantum.circuit`. Support circuits include at the moment a fast population count circuit to check Hamming weight (based on the Cuccaro adder) and a circuit to generate all states with a specific Hamming weight (based on butterfly network).

More info on my thesis can be found here https://drive.google.com/open?id=10uptXrKdvPmT-OU7VW5kdLivSjB4-zv1
