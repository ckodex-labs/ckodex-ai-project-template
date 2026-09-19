"""
Unit and Conformance Tests for Designed Recovery & Governed Replay (Rules #18, #33, #34).
"""

from pathlib import Path

import pytest

from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease
from ckodex_aiops.kernel.receipt import LineageReceipt
from ckodex_aiops.kernel.recovery import GovernedReplayRequest, RecoveryEngine
from ckodex_aiops.kernel.state_vector import OperationalLifecycle, StateVector, Valence


def test_checkpoint_save_and_verify(tmp_path: Path):
    engine = RecoveryEngine(checkpoints_dir=tmp_path / "checkpoints")

    # Create dummy artifact
    art = tmp_path / "weights.safetensors"
    art.write_bytes(b"dummy_weights_12345")

    # Save checkpoint
    ckpt = engine.save_checkpoint(
        run_id="run_100",
        node_name="train_node",
        state_vector=StateVector(lifecycle=OperationalLifecycle.NORMAL, valence=Valence.POSITIVE),
        artifact_paths=[art],
    )

    assert ckpt.checkpoint_id.startswith("ckpt_")
    assert len(ckpt.artifact_digests) == 1
    assert ckpt.canonical_digest() != ""

    # Verify intact checkpoint
    passed, msg, sv = engine.verify_checkpoint(ckpt.checkpoint_id)
    assert passed is True
    assert "verified" in msg.lower()
    assert sv.lifecycle == OperationalLifecycle.NORMAL

    # Tamper with artifact
    art.write_bytes(b"tampered_bytes_99999")
    passed_tampered, msg_tampered, sv_tampered = engine.verify_checkpoint(ckpt.checkpoint_id)
    assert passed_tampered is False
    assert "tamper" in msg_tampered.lower()
    assert sv_tampered.is_healthy() is False


def test_governed_replay(tmp_path: Path, monkeypatch):
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "ckodex_aiops.kernel.recovery.Path",
        lambda p: receipts_dir if "receipts" in str(p) else Path(p),
    )

    engine = RecoveryEngine(checkpoints_dir=tmp_path / "checkpoints")

    # Write a source receipt
    src_rcpt = LineageReceipt(
        receipt_id="rcpt_source_1",
        intent_id="intent_1",
        node_name="test_inference_node",
        authority_urn="urn:ckodex:cfyd:aiops:development:ckodex-aiops",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=10.0,
    )
    (receipts_dir / "rcpt_source_1.json").write_text(src_rcpt.to_json(), encoding="utf-8")

    req = GovernedReplayRequest(
        replay_id="rep_01",
        source_receipt_id="rcpt_source_1",
        caller_identity="principal:operator",
        authority=AuthorityPath(tenant="cfyd", workspace="aiops"),
        lease=CapabilityLease(capabilities=("pipeline:read", "pipeline:execute")),
        fenced_side_effects=("SIMULATION_MODE",),
    )

    new_rcpt = engine.execute_replay(req)
    assert new_rcpt.receipt_id.startswith("rcpt_replay_")
    assert new_rcpt.attributes["is_replay"] is True
    assert new_rcpt.attributes["source_receipt_id"] == "rcpt_source_1"


def test_replay_unauthorized_lease(tmp_path: Path):
    engine = RecoveryEngine(checkpoints_dir=tmp_path / "checkpoints")

    # Revoked lease
    revoked_lease = CapabilityLease(capabilities=("pipeline:read",), revoked=True)
    req = GovernedReplayRequest(
        replay_id="rep_unauth",
        source_receipt_id="rcpt_any",
        caller_identity="principal:unauth",
        authority=AuthorityPath(tenant="cfyd", workspace="aiops"),
        lease=revoked_lease,
    )

    with pytest.raises(PermissionError, match="revoked or expired"):
        engine.execute_replay(req)
