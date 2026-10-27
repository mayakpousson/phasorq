# PhasorQ Experiment Lab

[![PhasorQ CI Pipeline](https://github.com/mayakpousson/phasorq/actions/workflows/ci.yml/badge.svg)](https://github.com/mayakpousson/phasorq/actions/workflows/ci.yml)

PhasorQ helps students explore a small quantum experiment, compare two ways to compile it, and keep a reproducible record of what happened. It is a Streamlit teaching app and a paired simulation study. Its built-in runs use **fixed, synthetic five-qubit devices**, not live hardware or paid jobs. It uses no LLM API.

## Try the app

Install [uv](https://docs.astral.sh/uv/) and use Python 3.12:

```powershell
uv sync --group dev
uv run streamlit run src/app.py
```

Choose Bell state, three-qubit GHZ, or three-bit Bernstein–Vazirani. Pick a synthetic hardware profile and 256, 1,024, or 4,096 measurements, then select **Run comparison**. The app shows the ideal distribution and both observed distributions, compilation depth, two-qubit gate count, and distance from expected results. Lower distance means the measured bitstrings were closer to the ideal distribution; it is **not quantum-state fidelity**. A worse result for PhasorQ is shown as a worse result.

The default comparison uses Qiskit's standard layout selection. PhasorQ ranks qubits using a simple T2-to-single-qubit-error score and supplies that order as an initial layout for Qiskit's real topology-aware compiler. The compiler can add gates to make a proposal work; the health score is not a proven optimizer. The experiments use a bidirectional five-qubit line with either uniform or uneven synthetic errors. Qiskit Aer derives its noise model from the same device target used for compilation. All profiles are deterministic, versioned teaching examples.

The historic predictor in `src/analytics/predict.py` remains for reference and old tests. Its formula is an **unvalidated heuristic**, not a precise probability that a computation will produce a useful answer. The lab evaluates sampled outcomes instead.

## Keep and share experiments

The app keeps a history during one browser session. Download a JSON record to keep it; import it later to see the result again. CSV data and a standalone HTML report are also available. The JSON contains circuit identity, versioned profile, random seed, software versions, measurement counts, compilation statistics, and source. Imported hardware results are labeled as user imports because the public app cannot verify their origin. No account or database is required.

## Reproduce the study

```powershell
uv run pytest tests/
uv run python scripts/benchmark_simulation.py
```

The study runs three experiments × two profiles × three measurement counts × two compilation methods × ten seeds: **360 simulated trials, arranged as 180 matched pairs**. It saves row-level data to `results/simulation_runs.csv` and paired summaries to `results/simulation_summary.csv`. Both methods get the same device, measurement allowance, and seed. The summary includes ties and cases where either method loses. See [results/README.md](results/README.md) for interpretation and limitations. These are simulations, not 360 independent QPU experiments.

## Open Quantum hardware study

`notebooks/open_quantum_study.ipynb` documents a separate, opt-in validation study. The [Open Quantum Qiskit plugin](https://docs.openquantum.com/qiskit-plugin/overview/) can access a real processor, but credentials stay on the operator's own computer. The proposed study starts with Rigetti, uses public compute, reviews every preparation quote, and stays within a $10 equivalent Spark-credit ceiling. Hardware records can be imported into the website to compare their observed outputs with the ideal result. Live calibration is optional on Open Quantum, so synthetic noise must not be presented as a calibrated copy of a QPU. Public compute circuits are not confidential and published results require provider attribution; see [Open Quantum's terms](https://www.quantumrings.com/terms).

The website never requests Open Quantum credentials or submits a hardware job. The hardware study is separate from the simulation pilot and will be reported only after actual jobs have run.

## Project status

The simulation product and 360-trial benchmark are implemented. Hosting, the five-student usability study, real hardware observations, and a video walkthrough depend on external accounts or participants; results from those activities will be added when completed. [docs/pilot_protocol.md](docs/pilot_protocol.md) gives the user study procedure and success criteria.

This project does not claim financial savings, automatic quantum job blocking, a production service-level agreement, or improved hardware fidelity. Its purpose is to make experiment choices and limitations inspectable.

MIT License.
