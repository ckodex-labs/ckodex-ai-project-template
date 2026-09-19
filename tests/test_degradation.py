"""
Unit and Conformance Tests for Degraded Mode Contracts & Safe Hold (Rules #29, #30).
"""

from ckodex_aiops.kernel.degradation import (
    ContainmentScope,
    DegradationManager,
    DegradedModeContract,
    RuntimeMode,
)
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    StateVector,
    Valence,
)


def test_degraded_mode_contract_permits():
    contract = DegradedModeContract(
        contract_id="test-contract",
        name="Test Contract",
        trigger_condition="test",
        containment=ContainmentScope.READ_ONLY,
        residual_capabilities=("dataset:read", "model:infer"),
        prohibited_capabilities=("model:train", "dataset:write"),
        freshness_tolerance_seconds=60.0,
        security_guarantees=("Immutable read",),
        data_integrity_guarantees=("No corrupt checkpoints",),
        recovery_criteria=("Criteria met",),
    )

    assert contract.permits("dataset:read") is True
    assert contract.permits("model:infer") is True
    assert contract.permits("model:train") is False
    assert contract.permits("dataset:write") is False
    assert contract.permits("unspecified:cap") is False


def test_degradation_manager_anti_dominance_safe_hold():
    mgr = DegradationManager()

    # Normal vector
    normal_vec = StateVector(valence=Valence.POSITIVE, anti=Anti.NONE, coherence=Coherence.COHERENT)
    mode, contract, receipt = mgr.evaluate_vector(normal_vec)
    assert mode == RuntimeMode.NORMAL
    assert contract is None
    assert receipt is None

    # Anti-invariant violation MUST trigger SAFE_HOLD
    anti_vec = StateVector(valence=Valence.POSITIVE, anti=Anti.INVALIDATES)
    mode, contract, receipt = mgr.evaluate_vector(anti_vec)
    assert mode == RuntimeMode.SAFE_HOLD
    assert contract is not None
    assert contract.containment == ContainmentScope.BLOCKED_WRITES
    assert receipt is not None
    assert receipt.current_mode == RuntimeMode.SAFE_HOLD
    assert "Anti-invariant" in receipt.trigger_reason
    assert receipt.canonical_digest() != ""


def test_degradation_manager_decoherence_and_valence():
    mgr = DegradationManager()

    # Decoherence triggers SAFE_HOLD
    decoherent_vec = StateVector(coherence=Coherence.DECOHERENT)
    mode, contract, receipt = mgr.evaluate_vector(decoherent_vec)
    assert mode == RuntimeMode.SAFE_HOLD
    assert contract is not None
    assert receipt is not None

    # Adverse valence triggers DEGRADED
    adverse_vec = StateVector(
        valence=Valence.NEGATIVE, anti=Anti.NONE, coherence=Coherence.COHERENT
    )
    mode, contract, receipt = mgr.evaluate_vector(adverse_vec)
    assert mode == RuntimeMode.DEGRADED
    assert contract is not None
    assert contract.containment == ContainmentScope.READ_ONLY
    assert receipt is not None
