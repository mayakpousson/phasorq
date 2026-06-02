import numpy as np
from qiskit import QuantumCircuit

class PerformancePredictor:
    def __init__(self, avg_t1: float, avg_t2: float, avg_gate_error: float):
        """
        Initialize the predictor with current hardware telemetry metrics.
        Times are measured in microseconds (us).
        """
        self.avg_t1 = avg_t1
        self.avg_t2 = avg_t2
        self.avg_gate_error = avg_gate_error

    def calculate_circuit_esp(self, circuit: QuantumCircuit, gate_duration_us: float = 0.05) -> float:
        """
        Calculates the Estimated Success Probability (ESP) of a given quantum circuit.
        Fuses physical decoherence formulas with statistical gate failure rates.
        """
        # Count total operations (gates) in the circuit
        total_gates = sum(circuit.count_ops().values())
        
        # Calculate circuit depth to approximate execution duration
        circuit_depth = circuit.depth()
        total_duration = circuit_depth * gate_duration_us
        
        # 1. Calculate gate survival probability (statistical baseline)
        gate_survival = (1.0 - self.avg_gate_error) ** total_gates
        
        # 2. Calculate coherence survival probability based on physical decay limits (T1 and T2)
        coherence_survival = np.exp(-total_duration / self.avg_t1) * np.exp(-total_duration / self.avg_t2)
        
        # Total ESP is the compounded product of both survival rates
        esp = float(gate_survival * coherence_survival)
        
        # Guarantee boundaries are locked between absolute 0.0 and 1.0
        return round(max(0.0, min(esp, 1.0)), 4)