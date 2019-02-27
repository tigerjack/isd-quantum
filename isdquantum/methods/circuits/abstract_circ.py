import logging
from abc import ABC, abstractmethod, abstractproperty
from math import sqrt, pi, asin

_logger = logging.getLogger(__name__)


# Global: circuit, ancillas_list, inversion_qubits, n_func_domain, to_measure, rounds
class ISDAbstractCircuit(ABC):
    NWR_BENES = 'benes'
    NWR_FPC = 'fpc'
    NWR_MODES = (NWR_BENES, NWR_FPC)
    MCT_ADVANCED = 'advanced'
    MCT_BASIC = 'basic'
    MCT_NOANCILLA = 'noancilla'
    MCT_MODES = (MCT_ADVANCED, MCT_BASIC, MCT_NOANCILLA)

    def __init__(self, need_measures, mct_mode, nwr_mode, n_rounds):
        assert mct_mode in self.MCT_MODES, "Invalid mct_mode selected: {}".format(
            mct_mode)
        assert nwr_mode in self.NWR_MODES, "Invalid nwr_mode selected: {}".format(
            nwr_mode)
        self.need_measures = need_measures
        self.mct_mode = mct_mode
        self.nwr_mode = nwr_mode
        self.n_rounds = n_rounds
        _logger.info("measures: {}, mct_mode: {}, nwr_mode: {}".format(
            need_measures, mct_mode, nwr_mode))

    def build_circuit(self):
        n_rounds_computed = pi / (
            4 * asin(1 / sqrt(self.n_func_domain))) - 1 / 2
        _logger.debug("n rounds computed {}".format(n_rounds_computed))
        if self.n_rounds is not None and self.n_rounds > 0:
            self.rounds = self.n_rounds
        else:
            self.rounds = max(round(n_rounds_computed - 2e-1), 1)
        self.prepare_input()
        for i in range(self.rounds):
            _logger.debug("ITERATION {0}".format(i))
            self.oracle()
            self.prepare_input_i()
            self.diffusion()
            self.prepare_input()
            # #TODO delete after test
            # _logger.warning("BREAK ENABLED!!!!")
            # break

        if self.need_measures:
            from qiskit import ClassicalRegister
            cr = ClassicalRegister(len(self.to_measure), 'cols')
            self.circuit.add_register(cr)
            self.circuit.measure(self.to_measure, cr)
        return self.circuit

    @abstractmethod
    def oracle(self):
        pass

    @abstractmethod
    def prepare_input(self):
        # _logger.debug("Here")
        pass

    @abstractmethod
    def prepare_input_i(self):
        # _logger.debug("Here")
        pass

    # It rotates the states around zero, so the input state of the circuit
    # should be nearly zero
    def diffusion(self):
        # _logger.debug("Here")
        assert self.inversion_about_zero_qubits is not None, "Inversion about zero qubits must be initialized in subclasses"
        self.circuit.barrier()
        if len(self.inversion_about_zero_qubits) == 1:
            _logger.warn("Nothing to diffuse")
            return
        self.circuit.x(self.inversion_about_zero_qubits)

        # CZ = H CX H
        self.circuit.h(self.inversion_about_zero_qubits[0])
        self.circuit.mct(
            self.inversion_about_zero_qubits[1:],
            self.inversion_about_zero_qubits[0],
            self.ancillas_list,
            mode=self.mct_mode)
        self.circuit.h(self.inversion_about_zero_qubits[0])
        # CZ END

        self.circuit.x(self.inversion_about_zero_qubits)
        self.circuit.barrier()
