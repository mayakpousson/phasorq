import sys
import os
import time

# Permanent Path Configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
from qiskit import QuantumCircuit
from src.telemetry.broker import TelemetryBroker
from src.analytics.predict import PerformancePredictor
from src.compiler.router import NoiseAdaptiveRouter

# Page Configuration Architecture
st.set_page_config(page_title="PhasorQ Control Room", layout="wide", initial_sidebar_state="expanded")

st.title("PhasorQ: Noise-Adaptive Quantum Optimization Control Room")
st.caption("Enterprise Middleware UI Dashboard for Real-Time Qubit Telemetry & Co-Processing")
st.markdown("---")

# Sidebar Configuration for Hardware Profiling
st.sidebar.header("Hardware Configuration")
chip_size = st.sidebar.slider("Processor Scalability (Qubits)", min_value=3, max_value=12, value=5)

# Interactive Refresh Control Settings
st.sidebar.markdown("---")
st.sidebar.subheader("Live Automation Settings")
auto_refresh = st.sidebar.toggle("Enable Live Telemetry Polling", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (Seconds)", min_value=1, max_value=10, value=2)

# Circuit Selection Layout (Static UI Component)
st.subheader("Interactive Circuit Optimization Lab")
circuit_selection = st.selectbox(
    "Select Target Algorithm Workload",
    ["2-Qubit Bell State (Basic Validation)", "3-Qubit GHZ State (Entanglement Vector)", "5-Qubit QML Model Fragment (Complex Execution)"]
)

# Constructing selected circuit logical mapping
if "2-Qubit" in circuit_selection:
    qc = QuantumCircuit(2)
    qc.h(0); qc.cx(0, 1)
elif "3-Qubit" in circuit_selection:
    qc = QuantumCircuit(3)
    qc.h(0); qc.cx(0, 1); qc.cx(1, 2)
else:
    qc = QuantumCircuit(5)
    for i in range(5): qc.h(i)
    qc.cx(0, 4); qc.cx(1, 3)

st.markdown("---")

# AUTOMATION ENGINE FRAGMENT: This section auto-polls hardware metrics on a loop
@st.fragment
def render_live_telemetry_loop(chip_size: int, qc: QuantumCircuit, interval: int):
    # Fetch live fluctuating telemetry data
    broker = TelemetryBroker(num_qubits=chip_size)
    raw_telemetry_df = broker.fetch_live_hardware_metrics()
    system_averages = broker.extract_system_averages(raw_telemetry_df)
    
    # Executive High-Level Telemetry Metrics Panel
    st.subheader("System Hardware Health Snapshot")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Processor Mean T1 (Relaxation)", f"{system_averages['avg_t1']:.2f} µs")
    with metric_col2:
        st.metric("Processor Mean T2 (Dephasing)", f"{system_averages['avg_t2']:.2f} µs")
    with metric_col3:
        st.metric("Average Gate Error Rate", f"{system_averages['avg_gate_error']*100:.4f}%")

    # Analytical Visualization Engineering
    graph_col1, graph_col2 = st.columns(2)
    with graph_col1:
        fig_t1_t2 = px.bar(
            raw_telemetry_df, x="qubit_id", y=["t1_us", "t2_us"], barmode="group",
            title="Physical Coherence Lifetime Analysis (Microseconds)",
            labels={"value": "Time Duration (µs)", "qubit_id": "Physical Qubit ID"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_t1_t2, use_container_width=True)
    with graph_col2:
        fig_errors = px.line(
            raw_telemetry_df, x="qubit_id", y="gate_error_rate", markers=True,
            title="Physical Gate Operation Instability Rates (Probability)",
            labels={"gate_error_rate": "Error Probability", "qubit_id": "Physical Qubit ID"},
            template="plotly_dark"
        )
        st.plotly_chart(fig_errors, use_container_width=True)

    # Execution Pipeline Optimization Processing
    predictor = PerformancePredictor(
        avg_t1=system_averages["avg_t1"], 
        avg_t2=system_averages["avg_t2"], 
        avg_gate_error=system_averages["avg_gate_error"]
    )
    standard_esp = predictor.calculate_circuit_esp(qc)

    # PhasorQ Optimization Pass Execution
    router = NoiseAdaptiveRouter(raw_telemetry_df)
    optimized_qc = router.compile_to_healthy_layout(qc)

    # Extract statistics restricted to targeted optimal qubits from metadata dictionary lookup
    selected_qubit_ids = optimized_qc.metadata["optimal_layout"]
    filtered_df = raw_telemetry_df[raw_telemetry_df["qubit_id"].isin(selected_qubit_ids)]
    optimized_averages = broker.extract_system_averages(filtered_df)

    optimized_predictor = PerformancePredictor(
        avg_t1=optimized_averages["avg_t1"],
        avg_t2=optimized_averages["avg_t2"],
        avg_gate_error=optimized_averages["avg_gate_error"]
    )
    phasorq_esp = optimized_predictor.calculate_circuit_esp(optimized_qc)

    # Core Product Value Proposition Analytics Display
    result_col1, result_col2 = st.columns(2)
    with result_col1:
        st.info(f"### Standard Deployment Path\n* Targeted Physical Nodes: Arbitrary Selection\n* **Estimated Success Rate: {standard_esp*100:.2f}%**")
    with result_col2:
        yield_delta = (phasorq_esp - standard_esp) * 100
        st.success(f"### PhasorQ Protected Deployment Path\n* Isolated Optimal Nodes: **Qubits {selected_qubit_ids}**\n* **Estimated Success Rate: {phasorq_esp*100:.2f}%**\n* Optimization Performance Boost: **+{yield_delta:.2f}% Yield Increase**")

    # Handle looping constraint if toggle is enabled
    if auto_refresh:
        time.sleep(interval)
        st.rerun()

# Run the live telemetry looping engine fragment
render_live_telemetry_loop(chip_size, qc, refresh_interval)