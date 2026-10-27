"""Paired, reproducible circuit comparisons on illustrative noisy hardware."""

from importlib.metadata import version

import qiskit
from qiskit import transpile
from qiskit_aer import AerSimulator

from src.compiler.router import NoiseAdaptiveRouter
from src.experiments import EXPERIMENTS, build_circuit, outcome_distance
from src.profiles import PROFILES, build_backend, telemetry_frame
from src.records import (
    ExperimentConfig, ExperimentRecord, SHOT_OPTIONS, TrialResult, circuit_digest,
    validate_record,
)


METHODS = ("qiskit_default", "phasorq_layout")


def run_comparison(config: ExperimentConfig) -> ExperimentRecord:
    if config.experiment_key not in EXPERIMENTS or config.profile_key not in PROFILES:
        raise ValueError("Choose a supported experiment and hardware profile")
    if config.shots not in SHOT_OPTIONS or config.seed is None or config.seed < 0:
        raise ValueError("Choose a supported measurement count and nonnegative seed")

    profile = PROFILES[config.profile_key]
    backend = build_backend(profile)
    simulator = AerSimulator.from_backend(backend)
    logical = build_circuit(config.experiment_key)
    router = NoiseAdaptiveRouter(telemetry_frame(profile))
    trials = []
    for method in METHODS:
        if method == "qiskit_default":
            compiled = transpile(
                logical, backend=backend, optimization_level=1, seed_transpiler=config.seed
            )
            proposed_layout = None
        else:
            compiled = router.compile_to_healthy_layout(logical, backend, seed=config.seed)
            proposed_layout = compiled.metadata["proposed_layout"]
        counts = {str(key): int(value) for key, value in
                  simulator.run(compiled, shots=config.shots,
                                seed_simulator=config.seed).result().get_counts().items()}
        trial = TrialResult(
            method=method,
            counts=counts,
            distance=outcome_distance(counts, EXPERIMENTS[config.experiment_key].expected),
            depth=compiled.depth(),
            two_qubit_gates=sum(
                1 for instruction in compiled.data if instruction.operation.num_qubits == 2
            ),
            proposed_layout=proposed_layout,
            final_layout=(compiled.layout.final_index_layout(filter_ancillas=True)
                          if compiled.layout is not None else None),
        )
        trials.append(trial)
    record = ExperimentRecord(
        config=config, source="simulation", trials=trials,
        software={"qiskit": qiskit.__version__, "qiskit_aer": version("qiskit-aer")},
        metadata={"profile_name": profile.name, "profile_version": profile.version,
                  "device_topology": "bidirectional five-qubit line",
                  "transpiler_optimization_level": 1},
        circuit_sha256=circuit_digest(config.experiment_key),
    )
    validate_record(record)
    return record
