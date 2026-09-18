"""
Tests for Experiment Tracking & Observability Adapters (MLflow & Flight Recorder).
"""

from __future__ import annotations

import json
from pathlib import Path

from ckodex_aiops.adapters.tracking.composite import CompositeTracker
from ckodex_aiops.adapters.tracking.flight_recorder import FlightRecorderTracker
from ckodex_aiops.adapters.tracking.mlflow_adapter import MLflowTracker
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


def test_flight_recorder_lifecycle(tmp_path: Path):
    tracker = FlightRecorderTracker(base_dir=tmp_path / "flight_recorder")

    run_id = tracker.start_run(run_name="test_run", tags={"env": "pytest"})
    assert run_id.startswith("run_")

    tracker.log_params({"learning_rate": 0.001, "batch_size": 32})
    tracker.log_metrics({"accuracy": 0.95, "loss": 0.12}, step=1)

    vector = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE,
        anti=Anti.NONE,
        coherence=Coherence.COHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL,
    )
    tracker.log_state_vector(vector, step=1)

    dummy_artifact = tmp_path / "model.safetensors"
    dummy_artifact.write_bytes(b"dummy_safetensors_bytes")
    logged_uri = tracker.log_artifact(dummy_artifact, artifact_type="model")
    assert Path(logged_uri).exists()

    receipt = LineageReceipt(
        receipt_id="rcpt_unit_test",
        intent_id="intent_123",
        node_name="test_node",
        authority_urn="urn:ckodex:authority:test",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=42.0,
    )
    tracker.log_receipt(receipt)

    tracker.end_run(status="FINISHED")

    # Verify run artifacts on disk
    manifest = json.loads((tmp_path / "flight_recorder" / run_id / "run_manifest.json").read_text())
    assert manifest["status"] == "FINISHED"
    assert "duration_sec" in manifest


def test_mlflow_tracker(tmp_path: Path):
    tracker = MLflowTracker(
        experiment_name="pytest_experiment",
        tracking_uri=f"file://{tmp_path / 'mlruns'}",
    )
    run_id = tracker.start_run("mlflow_test_run", tags={"test": "true"})
    assert run_id != ""

    tracker.log_params({"optimizer": "AdamW", "epochs": 5})
    tracker.log_metrics({"val_loss": 0.25}, step=1)

    vector = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE,
        anti=Anti.NONE,
        coherence=Coherence.COHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL,
    )
    tracker.log_state_vector(vector, step=1)
    tracker.end_run(status="FINISHED")


def test_composite_tracker(tmp_path: Path):
    fr = FlightRecorderTracker(base_dir=tmp_path / "fr")
    ml = MLflowTracker(
        experiment_name="composite_test",
        tracking_uri=f"file://{tmp_path / 'mlruns'}",
    )
    composite = CompositeTracker(trackers=[fr, ml])

    run_id = composite.start_run("composite_run")
    assert run_id != ""

    composite.log_params({"lr": 1e-4})
    composite.log_metrics({"train_loss": 0.4}, step=1)
    composite.end_run()
