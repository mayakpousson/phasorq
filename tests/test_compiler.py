import pytest
import pandas as pd
from qiskit import QuantumCircuit
from src.compiler.router import NoiseAdaptiveRouter

@pytest.fixture
def mock_telemetry():
    """Generates a predictable hardware state with clear healthy vs. broken qubits."""
    data = [
        {"qubit_id": 0, "t1_us": 100.0, "t2_us": 80.0, "gate_error_rate": 0.001},  # Healthy
        {"qubit_id": 1, "t1_us": 12.0,  "t2_us": 5.0,  "gate_error_rate": 0.050},  # Noisy
        {"qubit_id": 2, "t1_us": 110.0, "t2_us": 95.0, "gate_error_rate": 0.0005}  # Ultra Elite
    ]
    return pd.DataFrame(data)

def test_router_selects_healthiest_qubits(mock_telemetry):
    router = NoiseAdaptiveRouter(mock_telemetry)
    
    # Act: Request the top 2 best qubits out of our 3 available tracks
    best_qubits = router.select_optimal_qubits(required_qubits=2)
    
    # Assert: Qubit 2 (Ultra Elite) and Qubit 0 (Healthy) should be prioritized over Qubit 1 (Noisy)
    assert 2 in best_qubits
    assert 0 in best_qubits
    assert 1 not in best_qubits

def test_router_raises_error_on_insufficient_qubits(mock_telemetry):
    router = NoiseAdaptiveRouter(mock_telemetry)
    qc = QuantumCircuit(5) # Circuit requires 5 qubits, but hardware dataframe only has 3
    
    with pytest.raises(ValueError):
        router.compile_to_healthy_layout(qc)