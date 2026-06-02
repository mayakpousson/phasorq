import pytest
import pandas as pd
from src.telemetry.broker import TelemetryBroker

def test_telemetry_broker_generates_valid_dataframe():
    # Arrange: Initialize a broker managing a 7-qubit chip
    broker = TelemetryBroker(num_qubits=7)
    
    # Act: Retrieve the hardware DataFrame
    df = broker.fetch_live_hardware_metrics()
    
    # Assert: Verify data structures match enterprise expectations
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 7
    assert "t1_us" in df.columns
    assert "gate_error_rate" in df.columns

def test_extract_system_averages_computes_correctly():
    # Arrange: Setup broker and get data
    broker = TelemetryBroker(num_qubits=5)
    df = broker.fetch_live_hardware_metrics()
    
    # Act: Process raw metrics into systemic metrics
    averages = broker.extract_system_averages(df)
    
    # Assert: Verify calculation properties hold true
    assert "avg_t1" in averages
    assert "avg_gate_error" in averages
    assert averages["avg_t1"] > 0
    assert 0.0 < averages["avg_gate_error"] < 1.0