"""
Unit tests for Pure Semantic Kernel.
Verifies invariants: Authority-born, Intent-native, Vector State, Lineage Receipts.
"""

from datetime import UTC, datetime

from ckodex_aiops.kernel.intent import (
    AuthorityPath,
    CapabilityLease,
    IntentEnvelope,
    IntentLifecycle,
)
from ckodex_aiops.kernel.receipt import EvidenceDigest, LineageReceipt, compute_sha256
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)


def test_authority_and_capability_lease():
    authority = AuthorityPath(tenant="cfyd", workspace="aiops", environment="prod", project="test")
    assert authority.to_urn() == "urn:ckodex:cfyd:aiops:prod:test"

    lease = CapabilityLease(
        capabilities=("pipeline:read", "pipeline:execute"),
        expires_at_epoch=datetime.now(UTC).timestamp() + 1000,
    )
    assert lease.is_valid()
    assert lease.permits("pipeline:execute")
    assert not lease.permits("model:delete")

    # Test revocation
    revoked_lease = CapabilityLease(capabilities=("pipeline:execute",), revoked=True)
    assert not revoked_lease.is_valid()
    assert not revoked_lease.permits("pipeline:execute")


def test_intent_envelope_transitions():
    intent = IntentEnvelope(
        actor="principal:engineer",
        requested_capability="pipeline:execute",
    )
    assert intent.lifecycle == IntentLifecycle.PROPOSED

    admitted = intent.transition(IntentLifecycle.ADMITTED)
    assert admitted.lifecycle == IntentLifecycle.ADMITTED
    assert admitted.intent_id == intent.intent_id


def test_state_vector_invariants():
    # Healthy state vector
    healthy = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE,
        anti=Anti.NONE,
        coherence=Coherence.COHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL,
    )
    assert healthy.is_healthy()

    # Hard invariant: ANTI dominates score
    anti_state = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE,
        anti=Anti.INVALIDATES,
        coherence=Coherence.COHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL,
    )
    assert not anti_state.is_healthy()

    # Decoherence dominates
    decoherent = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE,
        anti=Anti.NONE,
        coherence=Coherence.DECOHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL,
    )
    assert not decoherent.is_healthy()


def test_lineage_receipt_and_digest():
    digest = EvidenceDigest(
        algorithm="sha256", digest=compute_sha256("test-content"), uri="file://test"
    )
    receipt = LineageReceipt(
        receipt_id="rcpt_001",
        intent_id="intent_001",
        node_name="test_node",
        authority_urn="urn:ckodex:cfyd:aiops:test:run",
        input_digests=(),
        output_digests=(digest,),
        execution_duration_ms=45.2,
    )
    assert receipt.canonical_digest() is not None
    assert len(receipt.canonical_digest()) == 64
    d = receipt.to_dict()
    assert d["receipt_id"] == "rcpt_001"
