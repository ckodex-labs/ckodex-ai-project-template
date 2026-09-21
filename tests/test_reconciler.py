"""Tests for Autonomic Day-2 Reconciler & Self-Healing Engine.
Validates the canonical control loop: OBSERVE -> DETECT -> DIAGNOSE -> RECOVER -> RECONCILE.
"""

from __future__ import annotations

from ckodex_aiops.kernel.reconciler import AutonomicReconciler


def test_reconciler_observe_and_detect():
    """Reconciler must observe current storage and model files and detect drift."""
    reconciler = AutonomicReconciler(profile_name="macos_metal_safetensors")
    observed = reconciler.observe()

    assert "datasets" in observed
    assert "models" in observed
    assert observed["profile"] == "macos_metal_safetensors"

    anomalies = reconciler.detect(observed)
    assert isinstance(anomalies, list)


def test_reconciler_diagnose_state_vector():
    """Reconciler must correctly calculate state vector based on anomaly severity."""
    reconciler = AutonomicReconciler(profile_name="macos_metal_safetensors")

    # Empty anomalies -> NORMAL
    normal_vec = reconciler.diagnose([])
    assert normal_vec.is_healthy()
    assert normal_vec.lifecycle == "NORMAL"


def test_reconciler_full_loop():
    """Reconciler must execute full control loop and emit a cryptographic receipt."""
    reconciler = AutonomicReconciler(profile_name="macos_metal_safetensors")
    receipt = reconciler.run_reconciliation(auto_heal=True)

    assert receipt.receipt_id.startswith("rcpt_reconcile_")
    assert len(receipt.evidence_digest) == 64
    assert receipt.resulting_vector is not None


def test_reconciler_fragment_bloat_auto_heal(tmp_path):
    """Reconciler must auto-heal fragmented Lance tables via optimize.compact_files."""
    import lance
    import pyarrow as pa

    from ckodex_aiops.kernel.reconciler import AnomalyDetection

    # Create dummy dataset
    target = tmp_path / "fragmented.lance"
    schema = pa.schema([pa.field("id", pa.int32())])
    t1 = pa.Table.from_pydict({"id": [1, 2, 3]}, schema=schema)
    lance.write_dataset(t1, str(target), mode="create")

    # Append fragments
    for i in range(4):
        ti = pa.Table.from_pydict({"id": [i * 10, i * 10 + 1]}, schema=schema)
        lance.write_dataset(ti, str(target), mode="append")

    anomaly = AnomalyDetection(
        subsystem="storage_lance",
        anomaly_type="FRAGMENT_BLOAT",
        severity="MEDIUM",
        details={"dataset": str(target), "fragments": 5},
        remediation_action=f"compact_dataset:{target}",
        auto_healable=True,
    )

    reconciler = AutonomicReconciler(profile_name="macos_metal_safetensors")
    actions = reconciler.recover([anomaly], execute_heal=True)

    assert len(actions) == 1
    assert actions[0].startswith(f"HEALED_COMPACTED_FRAGMENTS:{target}")
    # Verify dataset remains readable after compaction
    ds = lance.dataset(str(target))
    assert ds.count_rows() == 11
