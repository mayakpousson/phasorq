import pandas as pd
from qiskit import QuantumCircuit

class NoiseAdaptiveRouter:
    def __init__(self, telemetry_df: pd.DataFrame):
        self.telemetry_df = telemetry_df

    def select_optimal_qubits(self, required_qubits: int) -> list[int]:
        if required_qubits > len(self.telemetry_df):
            raise ValueError(f"Circuit requires {required_qubits} qubits, but hardware only has {len(self.telemetry_df)} available.")

        df_copy = self.telemetry_df.copy()
        df_copy["health_score"] = df_copy["t2_us"] / (df_copy["gate_error_rate"] + 1e-6)
        sorted_qubits = df_copy.sort_values(by="health_score", ascending=False)
        return sorted_qubits["qubit_id"].head(required_qubits).tolist()

    def compile_to_healthy_layout(self, circuit: QuantumCircuit) -> QuantumCircuit:
        num_circuit_qubits = circuit.num_qubits
        optimal_physical_layout = self.select_optimal_qubits(num_circuit_qubits)

        optimized_circuit = circuit.copy()
        
        # CHANGED HERE: Storing layout in metadata dictionary instead of read-only property
        optimized_circuit.metadata = {"optimal_layout": optimal_physical_layout}
        
        return optimized_circuit