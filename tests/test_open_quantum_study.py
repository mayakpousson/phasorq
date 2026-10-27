import pytest

from src.open_quantum_study import (
    BACKEND, attach_job_id, check_spend, initialize_study, read_manifest,
)


def test_study_plan_creates_18_recoverable_jobs_without_credentials(tmp_path):
    path = initialize_study(tmp_path / "study")
    manifest = read_manifest(path)
    assert manifest["backend"] == BACKEND
    assert len(manifest["jobs"]) == 18
    assert all(job["status"] == "planned" and job["job_id"] is None
               for job in manifest["jobs"])
    assert len(list((path.parent / "circuits").glob("*.qasm"))) == 3
    with pytest.raises(FileExistsError):
        initialize_study(path.parent)


def test_spend_guard_counts_pending_jobs_and_spark_balance():
    manifest = {"spark_credit_cap": 5., "jobs": [
        {"status": "submitted", "quote_credits": 2.},
        {"status": "submission_pending", "quote_credits": 1.},
        {"status": "prepared", "quote_credits": 1.},
    ]}
    assert check_spend(manifest, spark_balance=3., cost=2.) == 5.
    with pytest.raises(RuntimeError):
        check_spend(manifest, spark_balance=3., cost=2.1)
    with pytest.raises(RuntimeError):
        check_spend(manifest, spark_balance=1., cost=2.)


def test_pending_submission_requires_manual_job_id_reconciliation(tmp_path):
    path = initialize_study(tmp_path / "study")
    manifest = read_manifest(path)
    manifest["jobs"][0].update(status="submission_pending", quote_credits=1.)
    from src.open_quantum_study import write_manifest
    write_manifest(path, manifest)
    entry_id = manifest["jobs"][0]["entry_id"]
    attach_job_id(path, entry_id, "provider-job-123")
    recovered = read_manifest(path)["jobs"][0]
    assert recovered["status"] == "submitted"
    assert recovered["job_id"] == "provider-job-123"
    with pytest.raises(ValueError):
        attach_job_id(path, entry_id, "different-job")
