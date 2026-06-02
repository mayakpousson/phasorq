import numpy as np
import pandas as pd

class TelemetryBroker:
    def __init__(self, num_qubits: int = 5):
        """
        Initializes the broker to track metrics across a multi-qubit quantum processor.
        """
        self.num_qubits = num_qubits

    def fetch_live_hardware_metrics(self) -> pd.DataFrame:
        """
        Simulates an API call to a quantum cloud provider (like IBM Quantum).
        Generates noisy, fluctuating, physical calibration data for individual qubits.
        """
        telemetry_data = []

        for qubit_id in range(self.num_qubits):
            # Base physics metrics with random environmental fluctuations (noise)
            # T1 values typically range from 50 to 150 microseconds
            t1_value = float(np.random.normal(100.0, 15.0))
            # T2 values are typically shorter than or equal to T1 due to phase decoherence
            t2_value = float(np.random.normal(80.0, 12.0))
            # Single-qubit gate error rates (e.g., 0.05% to 0.5%)
            gate_error = float(np.clip(np.random.normal(0.0015, 0.0005), 0.0001, 0.01))

            qubit_metrics = {
                "qubit_id": qubit_id,
                "t1_us": round(max(10.0, t1_value), 2),
                "t2_us": round(max(5.0, t2_value), 2),
                "gate_error_rate": round(gate_error, 5)
            }
            telemetry_data.append(qubit_metrics)

        # Convert the raw nested data into a structured data science DataFrame
        return pd.DataFrame(telemetry_data)

    def extract_system_averages(self, df: pd.DataFrame) -> dict:
        """
        Aggregates the raw per-qubit data into processor-wide telemetry averages.
        This provides the high-level metrics needed by the Analytics Engine.
        """
        if df.empty:
            raise ValueError("Telemetry data frame is empty. Cannot extract averages.")

        averages = {
            "avg_t1": float(df["t1_us"].mean()),
            "avg_t2": float(df["t2_us"].mean()),
            "avg_gate_error": float(df["gate_error_rate"].mean())
        }
        return averages