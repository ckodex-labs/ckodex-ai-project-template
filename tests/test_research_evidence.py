"""
Tests for CKODEX Research Evidence Protocol Tracker Adapter.
Verifies pure experiment tracking, trial lifecycle, observations, and opaque correlations.
"""

from __future__ import annotations

from pathlib import Path

from ckodex_aiops.adapters.tracking.research_evidence_adapter import (
    ResearchEvidenceTracker,
)
from ckodex_aiops.kernel.receipt import LineageReceipt
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)


def test_research_evidence_tracker_lifecycle(tmp_path: Path):
    db_file = tmp_path / "test_research_evidence.db"
    tracker = ResearchEvidenceTracker(
        experiment_name="unit-test-experiment",
        db_path=db_file,
    )

    if not tracker.is_available:
        # If repo is not in default discovery paths, adapter cleanly falls back to noop
        run_id = tracker.start_run(run_name="fallback_run")
        assert run_id == "noop_research_run"
        return

    # 1. Start run (Trial under revision)
    run_id = tracker.start_run(run_name="trial_1", tags={"batch_size": "32"})
    assert run_id.startswith("trial_")

    # 2. Log parameters (notes)
    tracker.log_params({"lr": 0.001, "architecture": "mlp"})

    # 3. Log metrics (observations)
    tracker.log_metrics({"accuracy": 0.94, "loss": 0.06}, step=0)

    # 4. Log State Vector
    vector = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE,
        anti=Anti.NONE,
        coherence=Coherence.COHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL,
    )
    tracker.log_state_vector(vector, step=0)

    # 5. Log artifact (opaque correlation)
    dummy_model = tmp_path / "model.safetensors"
    dummy_model.write_bytes(b"dummy safetensors content")
    logged_ref = tracker.log_artifact(dummy_model, artifact_type="model")
    assert logged_ref == str(dummy_model)

    # 6. Log lineage receipt (opaque correlation to verified lineage)
    receipt = LineageReceipt(
        receipt_id="rcpt_unit_research",
        intent_id="intent_unit_research",
        node_name="model_evaluation",
        authority_urn="urn:ckodex:authority:root",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=12.5,
    )
    tracker.log_receipt(receipt)

    # 7. End run
    tracker.end_run(status="FINISHED")

    # Verify db was created on disk
    assert db_file.exists()
