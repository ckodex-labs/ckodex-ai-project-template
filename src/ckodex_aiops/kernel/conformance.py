"""
Multi-Dimensional Conformance Vector Engine (CKODEX Rules #20, #21, #22).
Implements executable transition contracts:
delta(Pe, S0, X, C) = <d, O, S1, E, R>
Ensures hard invariants dominate scores and non-conformant states cannot be averaged away.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)


@dataclass(frozen=True)
class ConformanceEvaluationResult:
    """Outcome of an executable conformance transition vector evaluation."""

    dimension: str
    stimulus_name: str
    passed: bool
    disposition: str  # ADMIT, DENY, SAFE_HOLD, QUARANTINE, ESCALATE
    initial_vector: StateVector
    resulting_vector: StateVector
    obligations: list[str]
    evidence_collected: list[str]
    failure_reason: str | None = None


class ConformanceEngine:
    """
    Evaluates multi-dimensional conformance transition vectors against policy snapshots.
    """

    @classmethod
    def evaluate_structural_transition(
        cls,
        initial_state: StateVector,
        data_batch: list[dict[str, Any]],
        expected_keys: list[str],
    ) -> ConformanceEvaluationResult:
        """Evaluates structural schema conformance."""
        evidence: list[str] = ["schema_contract_inspected"]
        if not data_batch:
            res_vector = StateVector(
                presence=Presence.EMPTY,
                valence=Valence.NEGATIVE,
                anti=Anti.NONE,
                coherence=Coherence.COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.FAILED,
            )
            return ConformanceEvaluationResult(
                dimension="STRUCTURAL",
                stimulus_name="empty_batch_submission",
                passed=False,
                disposition="DENY",
                initial_vector=initial_state,
                resulting_vector=res_vector,
                obligations=["raise_schema_validation_error"],
                evidence_collected=evidence,
                failure_reason="Data batch is empty.",
            )

        # Check key presence
        first_row = data_batch[0]
        missing_keys = [k for k in expected_keys if k not in first_row]
        if missing_keys:
            res_vector = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEGATIVE,
                anti=Anti.CONTRADICTS,
                coherence=Coherence.DECOHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.SAFE_HOLD,
            )
            return ConformanceEvaluationResult(
                dimension="STRUCTURAL",
                stimulus_name="schema_mismatch",
                passed=False,
                disposition="DENY",
                initial_vector=initial_state,
                resulting_vector=res_vector,
                obligations=["quarantine_batch", "notify_pipeline_operator"],
                evidence_collected=evidence,
                failure_reason=f"Missing required schema keys: {missing_keys}",
            )

        res_vector = StateVector(
            presence=Presence.PRESENT,
            valence=Valence.POSITIVE,
            anti=Anti.NONE,
            coherence=Coherence.COHERENT,
            evidence=EvidenceStatus.VERIFIED,
            lifecycle=OperationalLifecycle.NORMAL,
        )
        return ConformanceEvaluationResult(
            dimension="STRUCTURAL",
            stimulus_name="valid_schema_batch",
            passed=True,
            disposition="ADMIT",
            initial_vector=initial_state,
            resulting_vector=res_vector,
            obligations=["admit_batch_for_feature_pipeline"],
            evidence_collected=evidence,
        )

    @classmethod
    def evaluate_adversarial_anti_transition(
        cls,
        initial_state: StateVector,
        is_lease_revoked: bool,
        is_signature_tampered: bool,
    ) -> ConformanceEvaluationResult:
        """
        CKODEX Rule #16 & #22: ANTI invariant dominance.
        An anti-state (e.g. executing with revoked lease or tampered signature)
        CANNOT be averaged away by positive metrics.
        """
        evidence: list[str] = ["cryptographic_lease_checked", "artifact_signature_verified"]

        if is_lease_revoked or is_signature_tampered:
            # Mandatory ANTI violation dominates
            res_vector = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEGATIVE,
                anti=Anti.INVALIDATES,
                coherence=Coherence.DECOHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.QUARANTINED,
                metadata={"reason": "Lease revoked or signature tampered."},
            )
            return ConformanceEvaluationResult(
                dimension="ADVERSARIAL_ANTI",
                stimulus_name="adversarial_tampering_stimulus",
                passed=False,
                disposition="QUARANTINE",
                initial_vector=initial_state,
                resulting_vector=res_vector,
                obligations=["freeze_execution", "revoke_egress", "preserve_forensic_evidence"],
                evidence_collected=evidence,
                failure_reason="Mandatory ANTI-invariant violation detected.",
            )

        res_vector = StateVector(
            presence=Presence.PRESENT,
            valence=Valence.POSITIVE,
            anti=Anti.NONE,
            coherence=Coherence.COHERENT,
            evidence=EvidenceStatus.VERIFIED,
            lifecycle=OperationalLifecycle.NORMAL,
        )
        return ConformanceEvaluationResult(
            dimension="ADVERSARIAL_ANTI",
            stimulus_name="valid_execution_boundary",
            passed=True,
            disposition="ADMIT",
            initial_vector=initial_state,
            resulting_vector=res_vector,
            obligations=["mint_execution_receipt"],
            evidence_collected=evidence,
        )

    @classmethod
    def evaluate_degradation_recovery_transition(
        cls,
        initial_state: StateVector,
        backend_available: bool,
        retry_exhausted: bool,
    ) -> ConformanceEvaluationResult:
        """
        CKODEX Rule #29 & #30: Explicit Runtime Degradation Contract.
        """
        evidence: list[str] = ["backend_health_probed"]

        if not backend_available:
            res_vector = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEUTRAL,
                anti=Anti.NONE,
                coherence=Coherence.PARTIALLY_COHERENT,
                evidence=EvidenceStatus.OBSERVED,
                lifecycle=OperationalLifecycle.DEGRADED,
                metadata={"degraded_mode": "local_cache_read_only"},
            )
            return ConformanceEvaluationResult(
                dimension="DEGRADATION",
                stimulus_name="upstream_backend_outage",
                passed=True,  # Successfully handled according to degraded contract
                disposition="SAFE_HOLD" if retry_exhausted else "ADMIT_WITH_OBLIGATIONS",
                initial_vector=initial_state,
                resulting_vector=res_vector,
                obligations=["enable_local_read_only_fallback", "emit_degradation_telemetry"],
                evidence_collected=evidence,
                failure_reason="Upstream service unavailable; operating in declared degraded mode."
                if retry_exhausted
                else None,
            )

        res_vector = StateVector(
            presence=Presence.PRESENT,
            valence=Valence.POSITIVE,
            anti=Anti.NONE,
            coherence=Coherence.COHERENT,
            evidence=EvidenceStatus.VERIFIED,
            lifecycle=OperationalLifecycle.NORMAL,
        )
        return ConformanceEvaluationResult(
            dimension="DEGRADATION",
            stimulus_name="upstream_backend_healthy",
            passed=True,
            disposition="ADMIT",
            initial_vector=initial_state,
            resulting_vector=res_vector,
            obligations=[],
            evidence_collected=evidence,
        )
