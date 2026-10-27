import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit.providers import BackendV2

class NoiseAdaptiveRouter:
    """Propose an initial layout from a simple score; Qiskit handles topology routing."""
    def __init__(self, telemetry_df: pd.DataFrame):
        self.telemetry_df = telemetry_df

    def select_optimal_qubits(self, required_qubits: int) -> list[int]:
        if required_qubits > len(self.telemetry_df):
            raise ValueError(f"Circuit requires {required_qubits} qubits, but hardware only has {len(self.telemetry_df)} available.")

        df_copy = self.telemetry_df.copy()
        df_copy["health_score"] = df_copy["t2_us"] / (df_copy["gate_error_rate"] + 1e-6)
        sorted_qubits = df_copy.sort_values(by="health_score", ascending=False)
        return sorted_qubits["qubit_id"].head(required_qubits).tolist()

    def compile_to_healthy_layout(
        self, circuit: QuantumCircuit, backend: BackendV2, seed: int = 42
    ) -> QuantumCircuit:
        num_circuit_qubits = circuit.num_qubits
        optimal_physical_layout = self.select_optimal_qubits(num_circuit_qubits)

        optimized_circuit = transpile(
            circuit, backend=backend, initial_layout=optimal_physical_layout,
            optimization_level=1, seed_transpiler=seed,
        )
        optimized_circuit.metadata = {
            **(circuit.metadata or {}), "proposed_layout": optimal_physical_layout,
        }
        return optimized_circuit
