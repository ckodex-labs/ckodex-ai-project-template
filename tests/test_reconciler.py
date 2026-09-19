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
