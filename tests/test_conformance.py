"""Tests for Multi-Dimensional Conformance Vector Engine.
Validates transition contracts delta(Pe, S0, X, C) = <d, O, S1, E, R>,
including structural bounds, adversarial ANTI dominance, and degradation contracts.
"""

from __future__ import annotations

from ckodex_aiops.kernel.conformance import ConformanceEngine
from ckodex_aiops.kernel.state_vector import Anti, OperationalLifecycle, StateVector


def test_structural_conformance_transitions():
    """Structural validator must reject empty or missing-key batches and admit valid schemas."""
    init_state = StateVector()

    # 1. Empty batch
    res_empty = ConformanceEngine.evaluate_structural_transition(
        init_state, [], expected_keys=["a", "b"]
    )
    assert not res_empty.passed
    assert res_empty.disposition == "DENY"
    assert res_empty.resulting_vector.lifecycle == OperationalLifecycle.FAILED

    # 2. Missing keys
    res_missing = ConformanceEngine.evaluate_structural_transition(
        init_state, [{"a": 1}], expected_keys=["a", "b"]
    )
    assert not res_missing.passed
    assert res_missing.disposition == "DENY"
    assert res_missing.resulting_vector.lifecycle == OperationalLifecycle.SAFE_HOLD

    # 3. Valid batch
    res_valid = ConformanceEngine.evaluate_structural_transition(
        init_state, [{"a": 1, "b": 2}], expected_keys=["a", "b"]
    )
    assert res_valid.passed
    assert res_valid.disposition == "ADMIT"
    assert res_valid.resulting_vector.lifecycle == OperationalLifecycle.NORMAL


def test_adversarial_anti_dominance():
    """ANTI invariant violations must dominate and force quarantine."""
    init_state = StateVector()

    # Tampered signature or revoked lease
    res_anti = ConformanceEngine.evaluate_adversarial_anti_transition(
        init_state, is_lease_revoked=True, is_signature_tampered=False
    )
    assert not res_anti.passed
    assert res_anti.disposition == "QUARANTINE"
    assert res_anti.resulting_vector.anti == Anti.INVALIDATES
    assert res_anti.resulting_vector.lifecycle == OperationalLifecycle.QUARANTINED
    assert "preserve_forensic_evidence" in res_anti.obligations


def test_degradation_recovery_contract():
    """Degradation contract must transition to DEGRADED and declare containment mode."""
    init_state = StateVector()

    res_deg = ConformanceEngine.evaluate_degradation_recovery_transition(
        init_state, backend_available=False, retry_exhausted=False
    )
    assert res_deg.passed
    assert res_deg.resulting_vector.lifecycle == OperationalLifecycle.DEGRADED
    assert "enable_local_read_only_fallback" in res_deg.obligations
