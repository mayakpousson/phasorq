import json

import pytest
from qiskit import transpile
from qiskit_aer import AerSimulator

from src.experiments import EXPERIMENTS, build_circuit, outcome_distance
from src.profiles import EDGES, PROFILES, build_backend
from src.records import (
    ExperimentConfig, imported_hardware_record, record_from_json, report_html, results_csv,
)
from src.runner import run_comparison
from scripts.benchmark_simulation import summarize_pairs
from src.hardware_import import import_open_quantum_result, normalize_counts
from src.records import circuit_digest


@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_ideal_experiments_have_expected_outcomes(key):
    circuit = build_circuit(key)
    counts = AerSimulator().run(circuit, shots=4096, seed_simulator=7).result().get_counts()
    assert outcome_distance(counts, EXPERIMENTS[key].expected) < 0.04


@pytest.mark.parametrize("profile_key", list(PROFILES))
def test_profile_properties_and_topology_are_shared(profile_key):
    profile = PROFILES[profile_key]
    backend = build_backend(profile)
    assert backend.target.qubit_properties[0].t1 == pytest.approx(profile.t1_us[0] * 1e-6)
    assert backend.target["cx"][(2, 3)].error == profile.two_qubit_error[2]
    assert set(backend.target["cx"]) == set(EDGES)


@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_comparison_is_paired_reproducible_and_topology_aware(key):
    config = ExperimentConfig(key, "uneven", 256, 42)
    first = run_comparison(config)
    second = run_comparison(config)
    assert [(t.method, t.counts, t.final_layout) for t in first.trials] == [
        (t.method, t.counts, t.final_layout) for t in second.trials
    ]
    assert len(first.trials) == 2
    assert all(sum(t.counts.values()) == 256 for t in first.trials)
    assert all(t.final_layout is not None for t in first.trials)
    # The compiled operation set must be supported by the device.
    backend = build_backend(PROFILES["uneven"])
    circuit = transpile(build_circuit(key), backend=backend, optimization_level=1,
                        seed_transpiler=42)
    assert set(circuit.count_ops()) <= set(backend.operation_names)


def test_export_import_and_reports_round_trip():
    record = run_comparison(ExperimentConfig("bell", "uniform", 256, 42))
    restored = record_from_json(record.to_json())
    assert restored == record
    assert "Distance from expected" in report_html(restored)
    assert "record_id,source" in results_csv(restored)


def test_invalid_hardware_record_rejected():
    with pytest.raises(ValueError):
        imported_hardware_record("bell", {"00": 128, "11": -1},
                                 job_id="job1", backend="rigetti")
    with pytest.raises(ValueError):
        imported_hardware_record("bell", {"0": 128}, job_id="job1", backend="rigetti")
    good = imported_hardware_record("bell", {"00": 128, "11": 128},
                                    job_id="job1", backend="rigetti")
    tampered = json.loads(good.to_json())
    tampered["circuit_sha256"] = "wrong"
    with pytest.raises(ValueError):
        record_from_json(json.dumps(tampered))


def test_hardware_record_keeps_unknown_metadata_unknown():
    record = imported_hardware_record("bv", {"101": 256}, job_id="job1",
                                      backend="rigetti")
    restored = record_from_json(record.to_json())
    assert restored.source == "imported_hardware"
    assert restored.metadata["charge"] is None
    assert restored.metadata["calibration"] is None
    assert restored.trials[0].distance == 0


def test_benchmark_summary_labels_wins_correctly():
    summary = summarize_pairs("bell", "uniform", 256,
                              [(0.2, 0.1), (0.1, 0.2), (0.1, 0.1)])
    assert summary["phasorq_closer"] == 1
    assert summary["qiskit_closer"] == 1
    assert summary["ties"] == 1
    assert summary["mean_phasorq_minus_qiskit"] == pytest.approx(0.)


def test_open_quantum_result_imports_with_explicit_identity_and_bit_order():
    record = import_open_quantum_result(
        experiment_key="bell", expected_circuit_sha256=circuit_digest("bell"),
        output={"counts": {"00": 130, "11": 126}}, shots=256,
        job_id="hardware-job-1", backend="rigetti:cepheus-1-108q",
        submitted_at_utc="2026-10-27T10:00:00Z",
    )
    assert record.source == "imported_hardware"
    assert record_from_json(record.to_json()) == record
    assert record.trials[0].counts == {"00": 130, "11": 126}
    assert record.metadata["submitted_at_utc"] == "2026-10-27T10:00:00Z"
    assert record.metadata["measurement_mapping"] == [
        {"classical_bit": 0, "logical_qubit": 0},
        {"classical_bit": 1, "logical_qubit": 1},
    ]


@pytest.mark.parametrize("output", [
    {"counts": {"0": 256}},
    {"counts": {"00": 255}},
    {"counts": {"00": -1, "11": 257}},
    {"counts": {"00": 128.0, "11": 128}},
    {"histogram": [128, 128]},
])
def test_open_quantum_import_rejects_unknown_or_inconsistent_output(output):
    with pytest.raises(ValueError):
        normalize_counts(output, measured_bits=2, expected_shots=256)


def test_open_quantum_import_rejects_circuit_mismatch():
    with pytest.raises(ValueError, match="does not match"):
        import_open_quantum_result(
            experiment_key="bell", expected_circuit_sha256="wrong",
            output={"00": 256}, shots=256, job_id="job", backend="rigetti",
        )
