"""Operator-run Open Quantum study; never imported by the public web app."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path

from qiskit import qasm2, transpile

from src.experiments import EXPERIMENTS, build_circuit
from src.hardware_import import import_open_quantum_result
from src.records import circuit_digest


BACKEND = "rigetti:cepheus-1-108q"
SPARK_CREDIT_CAP = 5.0  # Provider currently describes 25 Spark credits as $50 equivalent.
STUDY_SHOTS = (256, 1024)


def write_manifest(path: Path, manifest: dict) -> None:
    """Write job IDs before the next action so interrupted runs can be reconciled."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def read_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != 1 or manifest.get("backend") != BACKEND:
        raise ValueError("Unsupported study manifest or unexpected backend")
    return manifest


def initialize_study(directory: Path) -> Path:
    """Generate only public teaching circuits; this performs no API calls."""
    manifest_path = directory / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError("Study already exists; use its manifest rather than restarting")
    directory.mkdir(parents=True, exist_ok=True)
    circuits = directory / "circuits"
    circuits.mkdir(exist_ok=True)
    jobs = []
    for experiment_key in EXPERIMENTS:
        (circuits / f"{experiment_key}.qasm").write_text(
            qasm2.dumps(build_circuit(experiment_key)), encoding="utf-8"
        )
        for shots in STUDY_SHOTS:
            for repeat in range(1, 4):
                jobs.append({
                    "entry_id": f"{experiment_key}-{shots}-r{repeat}",
                    "experiment_key": experiment_key,
                    "circuit_sha256": circuit_digest(experiment_key),
                    "shots": shots, "repeat": repeat,
                    "status": "planned", "preparation_id": None, "job_id": None,
                    "quote_credits": None,
                })
    write_manifest(manifest_path, {"version": 1, "backend": BACKEND,
                                   "spark_credit_cap": SPARK_CREDIT_CAP, "jobs": jobs})
    return manifest_path


def _entry(manifest: dict, entry_id: str) -> dict:
    matches = [entry for entry in manifest["jobs"] if entry["entry_id"] == entry_id]
    if len(matches) != 1:
        raise ValueError("Unknown study entry")
    return matches[0]


def _clients():
    """Use only local environment credentials; never save or print secrets."""
    from openquantum_sdk.auth import ClientCredentials, ClientCredentialsAuth
    from openquantum_sdk.clients import ManagementClient, SchedulerClient

    client_id = os.environ.get("OPENQUANTUM_CLIENT_ID")
    client_secret = os.environ.get("OPENQUANTUM_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("Set OPENQUANTUM_CLIENT_ID and OPENQUANTUM_CLIENT_SECRET locally")
    auth = ClientCredentialsAuth(ClientCredentials(client_id, client_secret))
    management = ManagementClient(auth=auth)
    scheduler = SchedulerClient(auth=auth, management_client=management)
    return management, scheduler


def _organization_id(management) -> str:
    supplied = os.environ.get("OPENQUANTUM_ORGANIZATION_ID")
    if supplied:
        return supplied
    organizations = management.list_user_organizations(limit=20).organizations
    if len(organizations) != 1:
        raise RuntimeError("Set OPENQUANTUM_ORGANIZATION_ID when the account has multiple organizations")
    return organizations[0].id


def verify_target():
    """Check the selected device's availability and Qiskit compilation capability."""
    from openquantum_sdk.auth import ClientCredentials
    from openquantum_sdk_qiskit import OpenQuantumService

    client_id = os.environ.get("OPENQUANTUM_CLIENT_ID")
    client_secret = os.environ.get("OPENQUANTUM_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("Set OPENQUANTUM_CLIENT_ID and OPENQUANTUM_CLIENT_SECRET locally")
    with OpenQuantumService(
        creds=ClientCredentials(client_id, client_secret), auto_load=False
    ) as service:
        available = service.backends(name="rigetti", online=True)
        if not any(item.get("short_code") == BACKEND for item in available):
            raise RuntimeError(f"{BACKEND} is unavailable; postpone the study")
        backend = service.return_backend(BACKEND)
        for key in EXPERIMENTS:
            transpile(build_circuit(key), backend=backend, optimization_level=1,
                      seed_transpiler=42)
        return {"backend": BACKEND, "qubits": backend.num_qubits,
                "operations": sorted(backend.operation_names)}


def prepare(manifest_path: Path, entry_id: str) -> dict:
    """Upload and obtain a provider quote. Does not create a billable job."""
    from openquantum_sdk.models import JobPreparationCreate

    manifest = read_manifest(manifest_path)
    entry = _entry(manifest, entry_id)
    if entry["status"] != "planned":
        raise ValueError("This entry was already prepared or submitted")
    verify_target()
    management, scheduler = _clients()
    try:
        organization_id = _organization_id(management)
        qasm_path = manifest_path.parent / "circuits" / f"{entry['experiment_key']}.qasm"
        uploaded = scheduler.upload_job_input(file_path=str(qasm_path))
        preparation = scheduler.prepare_job(JobPreparationCreate(
            organization_id=organization_id, backend_class_id=BACKEND,
            name=f"PhasorQ {entry_id}", upload_endpoint_id=uploaded,
            job_subcategory_id="phys:oth", shots=entry["shots"], input_format="qasm",
        ))
        quote = scheduler.wait_for_preparation(preparation.id)
        selection = scheduler.choose_plan_and_priority(
            quote, execution_plan="public", queue_priority="standard"
        )
        entry.update(status="prepared", preparation_id=preparation.id,
                     quote_credits=selection.total_cost)
        write_manifest(manifest_path, manifest)
        return {"entry_id": entry_id, "plan": selection.plan_name,
                "priority": selection.priority_name, "quote_credits": selection.total_cost}
    finally:
        scheduler.close()
        management.close()


def check_spend(manifest: dict, spark_balance: float, cost: float) -> float:
    """Return reserved credits after this job, or refuse the spend."""
    reserved = sum(float(item["quote_credits"] or 0)
                   for item in manifest["jobs"]
                   if item["status"] in ("submission_pending", "submitted", "completed"))
    if cost < 0 or cost > spark_balance or reserved + cost > manifest["spark_credit_cap"]:
        raise RuntimeError("Quote exceeds available Spark credits or the study cap")
    return reserved + cost


def submit_prepared(manifest_path: Path, entry_id: str) -> str:
    """Submit after exact quote and Spark balance review; never resubmit pending jobs."""
    from openquantum_sdk.models import JobCreate

    manifest = read_manifest(manifest_path)
    entry = _entry(manifest, entry_id)
    if entry["status"] != "prepared" or not entry["preparation_id"]:
        raise ValueError("Only a prepared entry can be submitted; reconcile pending jobs by ID")
    management, scheduler = _clients()
    try:
        quote = scheduler.wait_for_preparation(entry["preparation_id"])
        selection = scheduler.choose_plan_and_priority(
            quote, execution_plan="public", queue_priority="standard"
        )
        organization_id = _organization_id(management)
        spark_balance = management.get_credit_balance(organization_id).spark_credits
        cost = float(selection.total_cost)
        reserved_after = check_spend(manifest, spark_balance, cost)
        print(f"{entry_id}: {selection.plan_name} / {selection.priority_name}; "
              f"exact quote {cost} Spark credits; study reserved after submission "
              f"{reserved_after}/{manifest['spark_credit_cap']}")
        if input(f"Type SUBMIT {entry_id} to create this hardware job: ").strip() != f"SUBMIT {entry_id}":
            raise RuntimeError("Submission canceled; no job created")
        entry.update(status="submission_pending", quote_credits=cost)
        write_manifest(manifest_path, manifest)
        job = scheduler.create_job(JobCreate(
            job_preparation_id=entry["preparation_id"],
            execution_plan_id=selection.execution_plan_id,
            queue_priority_id=selection.queue_priority_id,
            organization_id=organization_id,
        ))
        entry.update(status="submitted", job_id=job.id)
        write_manifest(manifest_path, manifest)
        return job.id
    finally:
        scheduler.close()
        management.close()


def attach_job_id(manifest_path: Path, entry_id: str, job_id: str) -> None:
    """Recover a submitted job found in the portal after an interrupted write."""
    manifest = read_manifest(manifest_path)
    entry = _entry(manifest, entry_id)
    if entry["status"] != "submission_pending" or not job_id.strip():
        raise ValueError("Only a pending submission can be reconciled")
    entry.update(status="submitted", job_id=job_id.strip())
    write_manifest(manifest_path, manifest)


def collect(manifest_path: Path, entry_id: str) -> Path | None:
    """Fetch a completed job by saved ID; preserve unrecognized raw output privately."""
    manifest = read_manifest(manifest_path)
    entry = _entry(manifest, entry_id)
    if entry["status"] not in ("submitted", "completed") or not entry["job_id"]:
        raise ValueError("No submitted job ID is saved for this entry")
    management, scheduler = _clients()
    try:
        job = scheduler.get_job(entry["job_id"])
        if job.status.lower() != "completed":
            print(f"{entry_id}: {job.status}; collect again later")
            return None
        raw_output = scheduler.download_job_output(job)
        raw_path = manifest_path.parent / "raw_outputs" / f"{entry_id}.json"
        raw_path.parent.mkdir(exist_ok=True)
        raw_path.write_text(json.dumps(raw_output, indent=2), encoding="utf-8")
        calibration = (scheduler.download_job_calibration(job)
                       if job.calibration_data_url else None)
        record = import_open_quantum_result(
            experiment_key=entry["experiment_key"],
            expected_circuit_sha256=entry["circuit_sha256"],
            output=raw_output, shots=entry["shots"], job_id=job.id, backend=BACKEND,
            submitted_at_utc=job.submitted_at, calibration=calibration,
        )
        output_path = manifest_path.parent / "records" / f"{entry_id}.json"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(record.to_json(), encoding="utf-8")
        entry["status"] = "completed"
        write_manifest(manifest_path, manifest)
        return output_path
    finally:
        scheduler.close()
        management.close()
