# Reproducible simulation study

Run `uv run python scripts/benchmark_simulation.py` from the repository root to regenerate both CSV files with Python 3.12 and the locked dependencies.

The dataset contains 360 trial rows arranged as 180 paired comparisons: three teaching circuits, two fixed synthetic hardware profiles, three shot counts, and ten random seeds. Each pair compares Qiskit's default compiler layout with an initial layout proposed by PhasorQ's simple T2/single-qubit-error score. Both circuits are compiled to the same five-qubit line and simulated against the same fixed noise model, with the same shot count and seed.

**Result:** Qiskit's default was closer to the ideal measured distribution in 89 pairs, PhasorQ in 30 pairs, and 61 tied. Under the uniform profile, Bell and GHZ often compile identically and tie. PhasorQ's proposal helped on the uneven GHZ case, but generally hurt Bell and Bernstein–Vazirani. The health score ignores two-qubit link quality and routing overhead; a layout can look healthy by its qubits yet require extra noisy gates. These results motivate a better scorer, not a claim of optimization.

The primary metric is **total variation distance** between the observed and ideal bitstring distributions. It ranges from zero to one, and lower is better. It does not measure quantum-state fidelity or verify entanglement. `simulation_runs.csv` stores every trial's metrics, actual final layout, circuit digest, and software versions. `simulation_summary.csv` stores per-condition means and matched win/loss/tie counts. `mean_phasorq_minus_qiskit` is negative when PhasorQ was closer.

The ten seeds vary sampling and compilation choices on two predetermined synthetic devices. They are not independent hardware calibrations or evidence of savings on a live processor. The methods also use the same seed but run as separate simulations; paired seeds make the comparison repeatable without eliminating sampling uncertainty. No dollars are modeled or claimed.
