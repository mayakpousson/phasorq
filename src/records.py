"""Portable experiment records used by the app, benchmark, and study notebook."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import csv
from hashlib import sha256
from html import escape
from io import StringIO
import json
from uuid import uuid4

from qiskit import qasm2

from src.experiments import EXPERIMENTS, build_circuit, outcome_distance
from src.profiles import PROFILES


SCHEMA_VERSION = 1
SHOT_OPTIONS = (256, 1024, 4096)


def circuit_digest(experiment_key: str) -> str:
    return sha256(qasm2.dumps(build_circuit(experiment_key)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_key: str
    profile_key: str | None
    shots: int
    seed: int | None


@dataclass(frozen=True)
class TrialResult:
    method: str
    counts: dict[str, int]
    distance: float
    depth: int | None = None
    two_qubit_gates: int | None = None
    proposed_layout: list[int] | None = None
    final_layout: list[int] | None = None


@dataclass(frozen=True)
class ExperimentRecord:
    config: ExperimentConfig
    source: str
    trials: list[TrialResult]
    software: dict[str, str]
    metadata: dict = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: str(uuid4()))
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: int = SCHEMA_VERSION
    measurement_order: str = "cN...c1c0"
    circuit_sha256: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["circuit_sha256"] = self.circuit_sha256 or circuit_digest(self.config.experiment_key)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def validate_record(record: ExperimentRecord) -> None:
    config = record.config
    if record.schema_version != SCHEMA_VERSION:
        raise ValueError("Unsupported experiment record version")
    if config.experiment_key not in EXPERIMENTS:
        raise ValueError("Unknown experiment in record")
    if record.source not in ("simulation", "imported_hardware"):
        raise ValueError("Unknown result source")
    if record.measurement_order != "cN...c1c0":
        raise ValueError("Unsupported measurement bit order")
    if record.circuit_sha256 and record.circuit_sha256 != circuit_digest(config.experiment_key):
        raise ValueError("Circuit identity does not match the selected experiment")
    if config.shots <= 0 or config.shots > 100000:
        raise ValueError("Invalid measurement count")
    if record.source == "simulation" and (config.profile_key not in PROFILES or config.seed is None):
        raise ValueError("Simulation profile or random seed is missing")
    if record.source == "imported_hardware" and (
        not record.metadata.get("job_id") or not record.metadata.get("backend")
    ):
        raise ValueError("Hardware job ID and backend are required")
    if not record.trials:
        raise ValueError("Record has no results")
    width = EXPERIMENTS[config.experiment_key].measured_bits
    expected = EXPERIMENTS[config.experiment_key].expected
    for trial in record.trials:
        if not trial.counts or sum(trial.counts.values()) != config.shots:
            raise ValueError("Measurement counts do not match the recorded shots")
        if any(type(count) is not int or count < 0 for count in trial.counts.values()):
            raise ValueError("Counts must be nonnegative integers")
        if any(len(bits) != width or set(bits) - {"0", "1"} for bits in trial.counts):
            raise ValueError("Measurement bitstrings have the wrong width or order")
        calculated = outcome_distance(trial.counts, expected)
        if abs(trial.distance - calculated) > 1e-9:
            raise ValueError("Recorded distance does not match the counts")


def record_from_json(raw: str | bytes) -> ExperimentRecord:
    if len(raw) > 2_000_000:
        raise ValueError("Experiment record is too large")
    try:
        data = json.loads(raw)
        config = ExperimentConfig(**data["config"])
        trials = [TrialResult(**item) for item in data["trials"]]
        record = ExperimentRecord(
            config=config, source=data["source"], trials=trials,
            software=data["software"], metadata=data.get("metadata", {}),
            record_id=data["record_id"], created_at_utc=data["created_at_utc"],
            schema_version=data["schema_version"],
            measurement_order=data["measurement_order"],
            circuit_sha256=data["circuit_sha256"],
        )
        validate_record(record)
        return record
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid experiment record") from exc


def imported_hardware_record(
    experiment_key: str, counts: dict[str, int], *, job_id: str, backend: str,
    created_at_utc: str | None = None, calibration: dict | None = None,
    charge: float | None = None, software: dict[str, str] | None = None,
) -> ExperimentRecord:
    shots = sum(counts.values())
    trial = TrialResult("hardware", counts, outcome_distance(counts, EXPERIMENTS[experiment_key].expected))
    record = ExperimentRecord(
        config=ExperimentConfig(experiment_key, None, shots, None),
        source="imported_hardware", trials=[trial], software=software or {},
        metadata={"job_id": job_id, "backend": backend, "calibration": calibration,
                  "charge": charge},
        created_at_utc=created_at_utc or datetime.now(timezone.utc).isoformat(),
        circuit_sha256=circuit_digest(experiment_key),
    )
    validate_record(record)
    return record


def results_csv(record: ExperimentRecord) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(("record_id", "source", "experiment", "method", "outcome", "count",
                     "shots", "distance_from_expected"))
    for trial in record.trials:
        for outcome, count in sorted(trial.counts.items()):
            writer.writerow((record.record_id, record.source, record.config.experiment_key,
                             trial.method, outcome, count, record.config.shots, trial.distance))
    return buffer.getvalue()


def report_html(record: ExperimentRecord) -> str:
    experiment = EXPERIMENTS[record.config.experiment_key]
    rows = "".join(
        f"<tr><td>{escape(trial.method)}</td><td>{trial.distance:.3f}</td>"
        f"<td>{escape(str(trial.depth) if trial.depth is not None else 'unknown')}</td>"
        f"<td>{escape(str(trial.two_qubit_gates) if trial.two_qubit_gates is not None else 'unknown')}</td>"
        f"<td>{escape(str(trial.counts))}</td></tr>" for trial in record.trials
    )
    source = "User-imported hardware result" if record.source == "imported_hardware" else "Synthetic simulation"
    note = ("This result was imported by a user; PhasorQ did not verify its provider provenance."
            if record.source == "imported_hardware" else
            "The noise profiles are illustrative and are not calibrated copies of a real processor.")
    return ("<!doctype html><html lang='en'><meta charset='utf-8'><title>PhasorQ report</title>"
            "<style>body{font:16px system-ui;max-width:850px;margin:2rem auto;padding:1rem;color:#18222b}"
            "table{border-collapse:collapse;width:100%}td,th{padding:.65rem;border:1px solid #aaa}"
            "th{text-align:left;background:#edf4f7}</style>"
            f"<h1>{escape(experiment.name)}</h1><p>{escape(experiment.question)}</p>"
            f"<p>{escape(experiment.explanation)}</p><p><strong>Source:</strong> {escape(source)}; "
            f"<strong>shots:</strong> {record.config.shots}; <strong>record:</strong> {escape(record.record_id)}</p>"
            f"<p>{escape(note)}</p><p>Ideal measured probabilities: {escape(str(experiment.expected))}</p>"
            "<table><thead><tr><th>Method</th><th>Distance from expected (lower is better)</th>"
            "<th>Depth</th><th>Two-qubit gates</th><th>Counts</th></tr></thead><tbody>"
            f"{rows}</tbody></table><p>Measurement bit order: {escape(record.measurement_order)}. "
            "Distance compares measured outcomes only; it is not quantum-state fidelity.</p>"
            "</html>")
