import logging
from abc import ABC, abstractmethod, abstractproperty
from math import sqrt, pi, asin

_logger = logging.getLogger(__name__)


class ISDAbstractCircuit(ABC):
    NWR_BENES = 'benes'
    NWR_FPC = 'fpc'
    NWR_MODES = (NWR_BENES, NWR_FPC)
    MCT_ADVANCED = 'advanced'
    MCT_BASIC = 'basic'
    MCT_NOANCILLA = 'noancilla'
    MCT_MODES = (MCT_ADVANCED, MCT_BASIC, MCT_NOANCILLA)

    def __init__(self, need_measures, mct_mode, nwr_mode):
        assert mct_mode in self.MCT_MODES, "Invalid mct_mode selected"
        assert nwr_mode in self.NWR_MODES, "Invalid nwr_mode selected"
        self.need_measures = need_measures
        self.mct_mode = mct_mode
        self.nwr_mode = nwr_mode
        # self.inversion_about_zero_qubits: list

    def build_circuit(self):
        rounds = pi / (4 * asin(1 / sqrt(self.n_func_domain))) - 1 / 2
        rounds = max(round(rounds), 1)
        self.prepare_input()
        for i in range(rounds):
            _logger.debug("ITERATION {0}".format(i))
            self.oracle()
            self.prepare_input_i()
            self.diffusion()
            self.prepare_input()

        if self.need_measures:
            from qiskit import ClassicalRegister
            cr = ClassicalRegister(len(self.to_measure), 'cols')
            self.circuit.add_register(cr)
            self.circuit.measure(self.to_measure, cr)
            # TODO just useful for tests to see the status of the registers
            # at the various stages
            # to_measure_2 = self.sum_q
            # cr2 = ClassicalRegister(len(to_measure_2))
            # self.circuit.add_register(cr2)
            # self.circuit.measure(to_measure_2, cr2)
            # to_measure_3 = self.lee_eq_q
            # cr3 = ClassicalRegister(len(to_measure_3))
            # self.circuit.add_register(cr3)
            # self.circuit.measure(to_measure_3, cr3)
            # if self.nwr_mode == 'benes':
            #     to_measure_4 = self.benes_flip_q
            #     cr4 = ClassicalRegister(len(to_measure_4))
            #     self.circuit.add_register(cr4)
            #     self.circuit.measure(to_measure_4, cr4)
            # elif self.nwr_mode == 'fpc':
            #     to_measure_4 = self.fpc_eq_q
            #     to_measure_5 = self.fpc_two_eq_q
            #     cr4 = ClassicalRegister(len(to_measure_4))
            #     self.circuit.add_register(cr4)
            #     self.circuit.measure(to_measure_4, cr4)
            #     cr5 = ClassicalRegister(len(to_measure_5))
            #     self.circuit.add_register(cr5)
            #     self.circuit.measure(to_measure_5, cr5)
        return self.circuit

    @abstractmethod
    def oracle(self):
        pass

    @abstractmethod
    def prepare_input(self):
        _logger.debug("Here")
        pass

    @abstractmethod
    def prepare_input_i(self):
        _logger.debug("Here")
        pass

    # It rotates the states around zero, so the input state of the circuit
    # should be nearly zero
    def diffusion(self):
        _logger.debug("Diffusion")
        assert self.inversion_about_zero_qubits is not None, "Inversion about zero qubits must be initialized in subclasses"
        self.circuit.barrier()
        self.circuit.x(self.inversion_about_zero_qubits)

        # CZ = H CX H
        self.circuit.h(self.inversion_about_zero_qubits[0])
        self.circuit.mct(
            self.inversion_about_zero_qubits[1:],
            self.inversion_about_zero_qubits[0],
            self.mct_anc,
            mode=self.mct_mode)
        self.circuit.h(self.inversion_about_zero_qubits[0])
        # CZ END

        self.circuit.x(self.inversion_about_zero_qubits)
        self.circuit.barrier()
