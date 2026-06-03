# PhasorQ: Noise-Adaptive Circuit Co-Processor & Compiler

[![PhasorQ CI Pipeline](https://github.com/mayakpousson/phasorq/actions/workflows/ci.yml/badge.svg)](https://github.com/mayakpousson/phasorq/actions/workflows/ci.yml)

PhasorQ is an enterprise-grade middleware optimization platform designed to safeguard cloud computing budgets and data execution fidelity for Quantum Machine Learning (QML) and cryptographic workloads. The system intercepts abstract quantum circuits, evaluates them against live hardware noise metrics, and dynamically rewrites the physical qubit layout mapping to execute exclusively on the highest-performing hardware tracks.

## The Problem (Market Context)
Unlike classical silicon microchips, quantum processors (QPUs) are incredibly fragile and prone to environmental interference. Thermal fluctuations, cosmic rays, and control-hardware drifts introduce phase decoherence and gate execution failures. 

Enterprise users deploying workflows via quantum cloud providers risk wasting costly computational allocations running circuits on physically degraded nodes, resulting in completely decayed calculations yielding random noise. Standard compilation engines fail to optimize for live, daily fluctuations in individual qubit error rates.

## The Solution (System Architecture)
PhasorQ operates as an intelligent, noise-adaptive middleware layer consisting of four modular decoupled tiers:

1. **Telemetry Broker (`src/telemetry/`):** Simulates live, real-time REST API telemetry pulls from multi-qubit physical backends. It leverages NumPy statistical distributions to model physical fluctuations in qubit noise and clean-structures raw streams into optimized Pandas DataFrames.
2. **Predictive Analytics Engine (`src/analytics/`):** Implements the official physical exponential decay laws of quantum mechanics. It parses abstract circuits, measures gate depth durations, and compounds statistical gate errors with physical $T_1$ (relaxation) and $T_2$ (dephasing) time constraints to calculate an Estimated Success Probability (ESP) before spending cloud capital.
3. **Noise-Adaptive Compiler (`src/compiler/`):** Evaluates the telemetry DataFrame via an algorithmic scoring heuristic ($\text{Health} = \frac{T_2}{\text{Error Rate}}$). It isolates the healthiest available qubit tracks and injects the physical layout routing configuration seamlessly into the circuit metadata.
4. **Interactive Control Room Dashboard (`src/app.py`):** An enterprise-grade, dark-mode analytical visualization layer powered by Streamlit and Plotly Express. It features an automated self-polling loop utilizing Streamlit fragment utilities to stream and plot real-time qubit parameter drifts, offering an interactive simulation environment for testing execution yield increases.

## Core Technology Stack & DevOps Rigor
* **Quantum Core:** Python 3.14, Qiskit SDK
* **Package Infrastructure:** Astral `uv` for deterministic dependency resolution and isolated caching.
* **Data Automation:** Pandas, NumPy, Plotly Express Data Visualization.
* **Client Interface:** Streamlit UI Architecture (Polled Self-Looping Streams).
* **Continuous Integration:** Automated GitHub Actions runner executing a strict 6-part test matrix via `pytest` on every commit, checking math validation and compiler constraints.