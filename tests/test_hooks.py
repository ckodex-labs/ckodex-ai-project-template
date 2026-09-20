"""
Tests for High-Assurance Kedro Hooks: Authority, Data Integrity, Resilience & Traceability.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl
import pytest
import torch
from kedro.pipeline.node import Node

from ckodex_aiops.hooks.authority_admission import AdmissionDeniedError, AuthorityAdmissionHook
from ckodex_aiops.hooks.data_integrity import DataCorruptionError, DataIntegrityHook
from ckodex_aiops.hooks.resilience_circuit import ResilienceCircuitBreakerHook
from ckodex_aiops.hooks.traceability_evidence import TraceabilityEvidenceHook
from ckodex_aiops.kernel.integrity import MerkleLineageChain
from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease, IntentEnvelope
from ckodex_aiops.kernel.receipt import LineageReceipt
from ckodex_aiops.kernel.resilience import CircuitBreakerOpenError


def _dummy_func(x):
    return x


def test_authority_admission_hook():
    hook = AuthorityAdmissionHook(strict_mode=True)
    mock_pipeline = MagicMock()
    mock_catalog = MagicMock()

    # 1. Normal execution admits
    hook.before_pipeline_run({}, mock_pipeline, mock_catalog)

    import time

    expired_lease = CapabilityLease(
        granted_to="test-runner",
        capabilities=("pipeline:execute",),
        expires_at_epoch=time.time() - 10.0,
    )
    expired_intent = IntentEnvelope(
        actor="test-runner",
        authority=AuthorityPath(
            tenant="cfyd", workspace="aiops", environment="test", project="ckx"
        ),
        requested_capability="pipeline:execute",
        lease=expired_lease,
    )
    hook.set_intent(expired_intent)

    with pytest.raises(AdmissionDeniedError, match="EXPIRED"):
        hook.before_pipeline_run({}, mock_pipeline, mock_catalog)

    # 3. Revoked lease denies
    revoked_lease = CapabilityLease(
        granted_to="test-runner",
        capabilities=("pipeline:execute",),
        revoked=True,
    )
    revoked_intent = IntentEnvelope(
        actor="test-runner",
        authority=AuthorityPath(
            tenant="cfyd", workspace="aiops", environment="test", project="ckx"
        ),
        requested_capability="pipeline:execute",
        lease=revoked_lease,
    )
    hook.set_intent(revoked_intent)

    with pytest.raises(AdmissionDeniedError, match="REVOKED"):
        hook.before_pipeline_run({}, mock_pipeline, mock_catalog)


def test_data_integrity_hook():
    hook = DataIntegrityHook(fail_on_corruption=True)
    node = Node(_dummy_func, "input_data", "output_data", name="test_node")

    # 1. Clean DataFrames pass
    clean_df = pl.DataFrame({"feature": [1.0, 2.0, 3.0]})
    hook.before_node_run(node, None, {"input_data": clean_df}, False)
    assert "test_node" in hook.last_node_input_digests
    assert len(hook.last_node_input_digests["test_node"]) == 1

    hook.after_node_run(node, None, {"input_data": clean_df}, {"output_data": clean_df}, False)
    assert "test_node" in hook.last_node_output_digests

    # 2. Empty DataFrame raises DataCorruptionError
    empty_df = pl.DataFrame({"feature": []})
    with pytest.raises(DataCorruptionError, match="EMPTY"):
        hook.before_node_run(node, None, {"input_data": empty_df}, False)

    # 3. NaN DataFrame raises DataCorruptionError
    nan_df = pl.DataFrame({"feature": [1.0, float("nan"), 3.0]})
    with pytest.raises(DataCorruptionError, match="NaN"):
        hook.before_node_run(node, None, {"input_data": nan_df}, False)

    # 4. Infinite Tensor raises DataCorruptionError
    inf_tensor = torch.tensor([1.0, float("inf")])
    with pytest.raises(DataCorruptionError, match="infinite"):
        hook.before_node_run(node, None, {"input_data": inf_tensor}, False)


def test_resilience_circuit_breaker_hook(tmp_path: Path):
    quarantine_dir = str(tmp_path / "quarantine")
    hook = ResilienceCircuitBreakerHook(
        failure_threshold=2,
        recovery_cooldown_seconds=10.0,
        quarantine_dir=quarantine_dir,
    )
    node = Node(_dummy_func, "inp", "out", name="fragile_node")

    # 1. Normal run succeeds
    hook.before_node_run(node, None, {}, False)
    hook.after_node_run(node, None, {}, {}, False)
    assert hook.get_breaker("fragile_node").failure_count == 0

    # 2. First failure
    err1 = ValueError("temporary blip")
    hook.on_node_error(err1, node, None, {}, False)
    assert hook.get_breaker("fragile_node").failure_count == 1
    # Check quarantine incident was written
    incidents = list(Path(quarantine_dir).glob("inc_*.json"))
    assert len(incidents) == 1

    # 3. Second failure trips circuit to OPEN
    err2 = RuntimeError("critical database fault")
    hook.on_node_error(err2, node, None, {}, False)
    assert hook.get_breaker("fragile_node").get_state().value == "OPEN"

    # 4. Execution while OPEN raises CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError, match="OPEN"):
        hook.before_node_run(node, None, {}, False)


def test_traceability_evidence_hook(tmp_path: Path):
    receipts_dir = str(tmp_path / "receipts")
    flight_file = str(tmp_path / "flight.jsonl")
    hook = TraceabilityEvidenceHook(
        output_dir=receipts_dir,
        flight_recorder_file=flight_file,
    )

    mock_pipeline = MagicMock()
    mock_catalog = MagicMock()
    hook.before_pipeline_run({}, mock_pipeline, mock_catalog)

    # First node run
    node1 = Node(_dummy_func, "in1", "out1", name="node_one")
    df1 = pl.DataFrame({"x": [1, 2, 3]})
    hook.before_node_run(node1, mock_catalog, {"in1": df1}, False)
    hook.after_node_run(node1, mock_catalog, {"in1": df1}, {"out1": df1}, False)

    # Second node run
    node2 = Node(_dummy_func, "out1", "out2", name="node_two")
    df2 = pl.DataFrame({"y": [4, 5, 6]})
    hook.before_node_run(node2, mock_catalog, {"out1": df1}, False)
    hook.after_node_run(node2, mock_catalog, {"out1": df1}, {"out2": df2}, False)

    # Verify receipts written
    r1_files = list(Path(receipts_dir).glob("*node_one.json"))
    r2_files = list(Path(receipts_dir).glob("*node_two.json"))
    assert len(r1_files) == 1
    assert len(r2_files) == 1

    # Load receipts and verify Merkle continuity
    with open(r1_files[0], encoding="utf-8") as f:
        r1_data = json.load(f)
    with open(r2_files[0], encoding="utf-8") as f:
        r2_data = json.load(f)

    r1 = LineageReceipt(**r1_data)
    r2 = LineageReceipt(**r2_data)

    # In r2, parent_receipt_digest should match r1's canonical digest
    assert r2.attributes["parent_receipt_digest"] == r1.canonical_digest()

    # Validate Merkle chain
    is_valid, violations = MerkleLineageChain.validate_chain([r1, r2])
    assert is_valid is True
    assert len(violations) == 0

    # Verify flight recorder file entries
    with open(flight_file, encoding="utf-8") as f:
        flight_lines = [json.loads(line) for line in f if line.strip()]
    assert len(flight_lines) == 2
    assert flight_lines[0]["node_name"] == "node_one"
    assert flight_lines[1]["node_name"] == "node_two"
