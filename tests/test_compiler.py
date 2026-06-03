import pytest
import pandas as pd
from qiskit import QuantumCircuit
from src.compiler.router import NoiseAdaptiveRouter

@pytest.fixture
def mock_telemetry():
    data = [
        {"qubit_id": 0, "t1_us": 100.0, "t2_us": 80.0, "gate_error_rate": 0.001},
        {"qubit_id": 1, "t1_us": 12.0,  "t2_us": 5.0,  "gate_error_rate": 0.050},
        {"qubit_id": 2, "t1_us": 110.0, "t2_us": 95.0, "gate_error_rate": 0.0005}
    ]
    return pd.DataFrame(data)

def test_router_selects_healthiest_qubits(mock_telemetry):
    router = NoiseAdaptiveRouter(mock_telemetry)
    best_qubits = router.select_optimal_qubits(required_qubits=2)
    assert 2 in best_qubits
    assert 0 in best_qubits
    assert 1 not in best_qubits

def test_compilation_attaches_correct_metadata(mock_telemetry):
    router = NoiseAdaptiveRouter(mock_telemetry)
    qc = QuantumCircuit(2)
    optimized_qc = router.compile_to_healthy_layout(qc)
    
    # CHANGED HERE: Verifies the data exists inside metadata
    assert "optimal_layout" in optimized_qc.metadata
    assert 2 in optimized_qc.metadata["optimal_layout"]