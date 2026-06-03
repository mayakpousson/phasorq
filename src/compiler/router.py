import pandas as pd
from qiskit import QuantumCircuit

class NoiseAdaptiveRouter:
    def __init__(self, telemetry_df: pd.DataFrame):
        """
        Initialize the compiler router with live, per-qubit hardware telemetry.
        """
        self.telemetry_df = telemetry_df

    def select_optimal_qubits(self, required_qubits: int) -> list[int]:
        """
        Analyzes the telemetry DataFrame to rank qubits by an engineering health score.
        Selects the top N healthiest physical qubits for circuit execution.
        """
        if required_qubits > len(self.telemetry_df):
            raise ValueError(f"Circuit requires {required_qubits} qubits, but hardware only has {len(self.telemetry_df)} available.")

        # PM Scoring Strategy: High T2 phase stability is premium. Lower error rate is premium.
        # We construct an algorithmic custom score: Health = (T2 / Gate Error Rate)
        df_copy = self.telemetry_df.copy()
        df_copy["health_score"] = df_copy["t2_us"] / (df_copy["gate_error_rate"] + 1e-6)

        # Sort qubits by healthiest first
        sorted_qubits = df_copy.sort_values(by="health_score", ascending=False)
        
        # Extract the native physical IDs of the highest-performing qubits
        optimal_ids = sorted_qubits["qubit_id"].head(required_qubits).tolist()
        return optimal_ids

    def compile_to_healthy_layout(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """
        Intercepts an abstract circuit and programmatically remaps its hardware layout
        to bind only to the healthiest physical qubit tracks available on the chip.
        """
        num_circuit_qubits = circuit.num_qubits
        optimal_physical_layout = self.select_optimal_qubits(num_circuit_qubits)

        # Create a clean, optimized copy of the circuit structure
        optimized_circuit = circuit.copy()
        
        # Attach the optimal hardware layout mapping metadata directly into the circuit instance
        optimized_circuit.layout = optimal_physical_layout
        
        return optimized_circuit