import pytest
import pandas as pd
from qiskit import QuantumCircuit
from src.compiler.router import NoiseAdaptiveRouter
from src.profiles import PROFILES, build_backend

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

def test_compilation_uses_proposed_layout_on_real_device_target(mock_telemetry):
    router = NoiseAdaptiveRouter(mock_telemetry)
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    optimized_qc = router.compile_to_healthy_layout(qc, build_backend(PROFILES["uneven"]))

    assert optimized_qc.metadata["proposed_layout"] == [2, 0]
    assert optimized_qc.layout is not None
    assert optimized_qc.count_ops().get("cx", 0) >= 1
