"""Conservative conversion of completed Open Quantum jobs into PhasorQ records."""

from collections.abc import Mapping

from src.experiments import EXPERIMENTS
from src.records import circuit_digest, imported_hardware_record


def normalize_counts(output: object, measured_bits: int, expected_shots: int) -> dict[str, int]:
    """Accept only explicit Qiskit-order bitstring counts; never guess bit order."""
    candidate = output
    if isinstance(candidate, Mapping) and "counts" in candidate:
        candidate = candidate["counts"]
    elif isinstance(candidate, Mapping) and "measurement_counts" in candidate:
        candidate = candidate["measurement_counts"]
    if not isinstance(candidate, Mapping) or not candidate:
        raise ValueError("No supported bitstring count map in the hardware result")
    counts = {}
    for bits, value in candidate.items():
        if not isinstance(bits, str) or len(bits) != measured_bits or set(bits) - {"0", "1"}:
            raise ValueError("Hardware output has unknown bit ordering or width")
        if type(value) is not int or value < 0:
            raise ValueError("Hardware counts must be nonnegative integers")
        counts[bits] = value
    if sum(counts.values()) != expected_shots:
        raise ValueError("Hardware counts do not add up to the recorded shots")
    return counts


def import_open_quantum_result(
    *, experiment_key: str, expected_circuit_sha256: str, output: object,
    shots: int, job_id: str, backend: str, submitted_at_utc: str | None = None,
    calibration: dict | None = None, charge: float | None = None,
) -> object:
    """Create a user-imported record from a job whose circuit was tracked locally."""
    if experiment_key not in EXPERIMENTS:
        raise ValueError("Unknown experiment")
    if expected_circuit_sha256 != circuit_digest(experiment_key):
        raise ValueError("Job manifest circuit does not match this experiment")
    if charge is not None and (not isinstance(charge, (int, float)) or charge < 0):
        raise ValueError("Invalid charge")
    counts = normalize_counts(output, EXPERIMENTS[experiment_key].measured_bits, shots)
    return imported_hardware_record(
        experiment_key, counts, job_id=job_id, backend=backend,
        submitted_at_utc=submitted_at_utc, calibration=calibration, charge=charge,
        software={"provider": "Open Quantum"},
    )
