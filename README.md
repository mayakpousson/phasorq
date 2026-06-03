# PhasorQ: Quantum Execution Governance and FinOps Middleware

[![PhasorQ CI Pipeline](https://github.com/mayakpousson/phasorq/actions/workflows/ci.yml/badge.svg)](https://github.com/mayakpousson/phasorq/actions/workflows/ci.yml)

PhasorQ is an enterprise-grade middleware optimization platform designed to safeguard cloud computing budgets and data execution fidelity for Quantum Machine Learning (QML) and cryptographic workloads. 

Unlike classical compilers that optimize strictly for low-level gate constraints, PhasorQ introduces execution governance and cost-containment as first-class compilation objectives, acting as an automated financial circuit breaker for multi-tenant quantum cloud networks.

---

## The Market Context: Why Existing Quantum Toolchains Fall Short

Quantum processors (QPUs) deployed via the cloud are highly volatile, suffering from continuous drifts in thermal fluctuations, relaxation times (T1), and dephasing times (T2). Current quantum SDKs and hardware-aware transpilers optimize strictly for:
* Gate count minimization
* Circuit depth reduction
* Topological routing feasibility

These platforms remain completely blind to execution economics. If an enterprise user submits a deep cryptographic or QML workload to a degrading hardware track, standard platforms will execute the circuit, consume the cloud capital, and return completely decayed calculations yielding random digital noise. 

PhasorQ shifts the paradigm from physics optimization to infrastructure asset management, treating execution fidelity as an economic resource. It evaluates computational viability before runtime execution, dynamically routing workloads to high-performing hardware tracks or halting economically dead operations completely.

---

## System Architecture

PhasorQ operates as an intelligent, noise-adaptive middleware layer consisting of four modular, decoupled tiers:

* **Telemetry Broker (src/telemetry/)**
  The Telemetry Broker simulates real-time REST API telemetry streams from physical multi-qubit backends. It utilizes NumPy statistical distributions to accurately model ongoing physical calibration parameter drifts. The raw data streams are then cleaned and structured into highly optimized Pandas DataFrames for downstream consumption.

* **Predictive Analytics Engine (src/analytics/)**
  The Predictive Analytics Engine implements the official physical exponential decay laws of quantum mechanics to evaluate abstract circuits. It calculates overall hardware execution time by accurately measuring cumulative gate depth durations. By compounding statistical gate errors with physical hardware relaxation and dephasing rates, the engine computes a precise Estimated Success Probability before any cloud capital is expended.

* **Noise-Adaptive Compiler (src/compiler/)**
  The Noise-Adaptive Compiler evaluates the incoming telemetry datasets via specialized algorithmic scoring heuristics. It assigns precise health scores to individual physical hardware tracks based on current operational error thresholds. This process isolates the highest-performing qubit paths and injects the optimal hardware routing layout seamlessly into the circuit metadata.

* **Interactive Control Room (src/app.py)**
  The Interactive Control Room provides an enterprise-grade dark-mode analytical visualization layer for monitoring system performance. This web interface is built using Streamlit and utilizes Plotly Express for rendering automated data visualizations. It leverages looping execution fragments to continuously stream hardware calibration shifts, allowing users to test execution yield increases in a safe simulation environment.

---

## Execution Governance Benchmark

To validate PhasorQ's access-control routing mechanism, the platform was benchmarked against a standard industry cloud deployment pipeline using a simulated 7-qubit noisy backend (tests/benchmark_novelty.py). 

Rather than focusing on incremental gate optimization, the benchmark tracks governance decisions as circuit complexity scales:


| Circuit Depth | Baseline Decision | PhasorQ Decision | Baseline Waste | PhasorQ Waste | Capital Saved |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **10** | EXECUTED (84.7% ESP) | EXECUTED (84.7% ESP) | \$0.00 | \$0.00 | \$0.00 |
| **50** | EXECUTED (43.7% ESP) | EXECUTED (43.7% ESP) | \$0.00 | \$0.00 | \$0.00 |
| **100** | EXECUTED (19.1% ESP) | EXECUTED (19.1% ESP) | \$0.00 | \$0.00 | \$0.00 |
| **150** | EXECUTED (8.3% ESP) | BLOCKED / REROUTED | \$1.00 | \$0.00 | \$1.00 |
| **250** | EXECUTED (1.6% ESP) | BLOCKED / REROUTED | \$1.00 | \$0.00 | \$1.00 |

### Insights from the Matrix
* Standard compilation tools blindly run deep workloads even when they fall far below viable execution thresholds. This results in a complete loss of allocated operational capital on corrupted calculations.
* The PhasorQ governance engine flags sub-threshold workloads before runtime submission occurs. It instantly halts risky jobs to enforce strict budget conservation rules and protect enterprise infrastructure SLAs.

---

## Tooling and DevOps Rigor

* The quantum core is built using Python 3.14 and leverages the core elements of the Qiskit SDK framework.
* Package infrastructure is managed via Astral uv for fast, deterministic dependency resolution and isolated local environment caching.
* Heavy data automation, statistical distribution modeling, and system profiling are driven entirely by Pandas and NumPy.
* The frontend client interface utilizes a clean Streamlit UI architecture built around polished self-looping web streams.
* The automated continuous integration pipeline relies on GitHub Actions to execute a strict multi-part test matrix using pytest on every commit.

---

## Engineering Roadmap

To transition PhasorQ into a multi-cloud enterprise production platform, future development targets three distinct milestones:

1. **Dynamic Topology Mapping and Graph Integration**
   The platform will integrate native Qiskit hardware CouplingMap graphs directly into the optimization router. This addition will allow the system to calculate the precise financial and gate-error penalties associated with mandatory physical SWAP gate injections on restricted physical hardware layouts.

2. **Moving Target Defense (MTD) Circuit Obfuscation**
   The compilation layer will be upgraded to programmatically shuffle layout mappings across random, varying subsets of healthy physical qubits on every runtime iteration. This mechanism randomizes physical hardware emissions to successfully neutralize side-channel pulse and thermal snooping attacks.

3. **Post-Quantum Cryptography (PQC) Profiling**
   The analytics infrastructure will expand to profile NIST-approved post-quantum cryptographic primitives such as ML-KEM/Kyber or ML-DSA/Dilithium. This feature will allow corporate security teams to benchmark data-fidelity margins before deploying quantum-resistant code onto noisy public cloud co-processors.
```