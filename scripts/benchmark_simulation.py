"""Reproduce the 360-trial paired simulation study.

Run from the project root: uv run python scripts/benchmark_simulation.py
"""

from collections import defaultdict
import argparse
import csv
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiments import EXPERIMENTS
from src.profiles import PROFILES
from src.records import ExperimentConfig, SHOT_OPTIONS
from src.runner import run_comparison


def summarize_pairs(experiment: str, profile: str, shots: int,
                    comparisons: list[tuple[float, float]]) -> dict:
    """A negative gap means PhasorQ was closer to the expected distribution."""
    baseline = [item[0] for item in comparisons]
    alternative = [item[1] for item in comparisons]
    gaps = [alternative_distance - baseline_distance
            for baseline_distance, alternative_distance in comparisons]
    return {
        "experiment": experiment, "profile": profile, "shots": shots,
        "paired_seeds": len(comparisons),
        "qiskit_mean_distance": statistics.mean(baseline),
        "phasorq_mean_distance": statistics.mean(alternative),
        "mean_phasorq_minus_qiskit": statistics.mean(gaps),
        "gap_stdev": statistics.stdev(gaps) if len(gaps) > 1 else 0.,
        "phasorq_closer": sum(gap < -1e-12 for gap in gaps),
        "qiskit_closer": sum(gap > 1e-12 for gap in gaps),
        "ties": sum(abs(gap) <= 1e-12 for gap in gaps),
    }


def run_study(seeds: int, output_dir: Path) -> tuple[Path, Path]:
    if seeds < 1:
        raise ValueError("At least one seed is required")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    paired = defaultdict(list)
    for experiment_key in EXPERIMENTS:
        for profile_key in PROFILES:
            for shots in SHOT_OPTIONS:
                for seed in range(seeds):
                    record = run_comparison(
                        ExperimentConfig(experiment_key, profile_key, shots, seed)
                    )
                    baseline, alternative = record.trials
                    paired[(experiment_key, profile_key, shots)].append(
                        (baseline.distance, alternative.distance)
                    )
                    for trial in record.trials:
                        rows.append({
                            "experiment": experiment_key, "profile": profile_key,
                            "profile_version": record.metadata["profile_version"],
                            "shots": shots, "seed": seed, "method": trial.method,
                            "distance_from_expected": trial.distance,
                            "depth": trial.depth, "two_qubit_gates": trial.two_qubit_gates,
                            "proposed_layout": trial.proposed_layout,
                            "final_layout": trial.final_layout,
                            "circuit_sha256": record.circuit_sha256,
                            "qiskit_version": record.software["qiskit"],
                            "aer_version": record.software["qiskit_aer"],
                        })
    runs_path = output_dir / "simulation_runs.csv"
    with runs_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summaries = []
    for (experiment, profile, shots), comparisons in paired.items():
        summaries.append(summarize_pairs(experiment, profile, shots, comparisons))
    summary_path = output_dir / "simulation_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    return runs_path, summary_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    runs, summary = run_study(args.seeds, args.output_dir)
    print(f"Saved {3 * 2 * 3 * 2 * args.seeds} trial rows to {runs}")
    print(f"Saved paired summary to {summary}")
