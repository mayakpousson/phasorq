import pytest
from qiskit import QuantumCircuit
from src.analytics.predict import PerformancePredictor

def test_perfect_hardware_yields_high_esp():
    # Setup an idealized backend with minimal noise
    predictor = PerformancePredictor(avg_t1=1000.0, avg_t2=1000.0, avg_gate_error=0.0001)
    
    # Create a standard 2-qubit Bell state quantum circuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    
    esp = predictor.calculate_circuit_esp(qc)
    
    # Perfect hardware should maintain high execution survival rates
    assert esp > 0.95

def test_noisy_hardware_degrades_esp():
    # Setup a highly degraded, noisy hardware environment
    noisy_predictor = PerformancePredictor(avg_t1=5.0, avg_t2=2.0, avg_gate_error=0.05)
    
    # Create the identical circuit configuration
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    
    esp = noisy_predictor.calculate_circuit_esp(qc)
    
    # Severe noise limits must drastically penalize execution success
    assert esp < 0.90