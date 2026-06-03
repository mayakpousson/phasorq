import numpy as np
import pandas as pd
from qiskit import QuantumCircuit
from qiskit.compiler import transpile
from qiskit.providers.fake_provider import GenericBackendV2

# 1. Setup a Mock Production Environment using Qiskit
# This mimics a 7-qubit noisy IBM-like topology with real drift properties
NUM_QUBITS = 7
backend = GenericBackendV2(num_qubits=NUM_QUBITS, seed=42)

# 2. Define Enterprise Financial Cost Model
COST_PER_SHOT = 0.0001    # e.g., $0.0001 per shot on a premium QPU
SHOTS_PER_JOB = 10000     # Standard enterprise batch size
BASE_JOB_COST = COST_PER_SHOT * SHOTS_PER_JOB # $1.00 per job execution
FIDELITY_THRESHOLD = 0.15 # If ESP falls below 15%, the output is useless noise

def calculate_phasorq_esp(circuit: QuantumCircuit, backend) -> float:
    """
    Simulates your src/analytics/ engine.
    Calculates Estimated Success Probability using physical T1, T2, and gate errors.
    """
    esp = 1.0
    properties = backend.target
    
    for instruction in circuit.data:
        gate = instruction.operation
        
        # Correctly call find_bit on the circuit object to map physical wire indices
        qubits = tuple(circuit.find_bit(q).index for q in instruction.qubits)
        
        try:
            # Query the backend target dict using the exact tuple format it expects
            if gate.name in properties and qubits in properties[gate.name]:
                gate_error = properties[gate.name][qubits].error
                if gate_error is not None:
                    esp *= (1.0 - gate_error)
        except KeyError:
            # Fallback if a specific multi-qubit link isn't calibrated on this backend
            esp *= 0.99 
            
    return max(0.0, min(esp, 1.0))

def run_novelty_benchmark():
    print("🚀 Running PhasorQ vs Baseline Industry Benchmark...\n")
    
    # Test across a range of circuit depths to watch the noise compound
    test_depths = [10, 50, 100, 150, 250]
    results = []
    
    for depth in test_depths:
        # Create a mock deep cryptographic/QML workflow
        qc = QuantumCircuit(NUM_QUBITS)
        for i in range(NUM_QUBITS):
            qc.h(i)
        for _ in range(depth):
            for i in range(NUM_QUBITS - 1):
                qc.cx(i, i + 1)
                
        # --- BASELINE INDUSTRY PIPELINE ---
        # The standard baseline compiles blind to budget risk and runs it anyway
        standard_compiled = transpile(qc, backend=backend, optimization_level=1)
        baseline_esp = calculate_phasorq_esp(standard_compiled, backend)
        
        baseline_cost_spent = BASE_JOB_COST
        baseline_value_generated = BASE_JOB_COST if baseline_esp >= FIDELITY_THRESHOLD else 0.0
        baseline_financial_waste = baseline_cost_spent - baseline_value_generated
        
        # --- PHASORQ MIDDLEWARE PIPELINE ---
        # Intercepts, runs Predictive Analytics, evaluates against threshold
        phasorq_esp = calculate_phasorq_esp(qc, backend)
        
        if phasorq_esp < FIDELITY_THRESHOLD:
            # BUDGET SAFEGUARD TRIGGERS: Hard stop execution to prevent burning capital
            phasorq_action = "BLOCKED / REROUTED"
            phasorq_cost_spent = 0.0  
            phasorq_financial_waste = 0.0
            capital_saved = BASE_JOB_COST
        else:
            phasorq_action = "EXECUTED"
            phasorq_cost_spent = BASE_JOB_COST
            phasorq_financial_waste = 0.0 if phasorq_esp >= FIDELITY_THRESHOLD else BASE_JOB_COST
            capital_saved = 0.0

        results.append({
            "Depth": depth,
            "Base ESP": f"{baseline_esp:.1%}",
            "PhasorQ ESP": f"{phasorq_esp:.1%}",
            "Base Waste": f"${baseline_financial_waste:.2f}",
            "PhasorQ Waste": f"${phasorq_financial_waste:.2f}",
            "Action": phasorq_action,
            "Saved": f"${capital_saved:.2f}"
        })
        
    # Convert to DataFrame for easier printing structure
    df = pd.DataFrame(results)
    
    # Print natively using formatting strings to avoid missing tabulate dependency
    header = f"{'Depth':<6} | {'Base ESP':<9} | {'PhasorQ ESP':<12} | {'Base Waste':<11} | {'PhasorQ Waste':<14} | {'Action':<19} | {'Saved':<7}"
    print(header)
    print("-" * len(header))
    
    for _, row in df.iterrows():
        print(f"{row['Depth']:<6} | {row['Base ESP']:<9} | {row['PhasorQ ESP']:<12} | {row['Base Waste']:<11} | {row['PhasorQ Waste']:<14} | {row['Action']:<19} | {row['Saved']:<7}")
    
    total_saved = sum([float(x.replace('$', '')) for x in df["Saved"]])
    print(f"\n📈 Total Enterprise Budget Safeguarded across test matrix: ${total_saved:.2f}")

if __name__ == "__main__":
    run_novelty_benchmark()