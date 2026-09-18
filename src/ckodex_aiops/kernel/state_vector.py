"""
Pure Semantic Kernel: State Vector & Conformance Primitives.
Complies with CKODEX Architectural Signature: Vector State, Not Booleans.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Presence(StrEnum):
    EMPTY = "EMPTY"  # No value/evidence exists
    PRESENT = "PRESENT"  # Explicit value exists
    UNKNOWN = "UNKNOWN"  # Cannot presently be established
    REDACTED = "REDACTED"  # Exists but withheld by policy


class Valence(StrEnum):
    POSITIVE = "POSITIVE"  # Supports proposition / invariant
    NEGATIVE = "NEGATIVE"  # Valid adverse evidence (not necessarily malicious)
    NEUTRAL = "NEUTRAL"  # Neither favorable nor adverse
    MIXED = "MIXED"  # Divergent indications
    UNRESOLVED = "UNRESOLVED"  # Pending resolution


class Anti(StrEnum):
    NONE = "NONE"  # No contradiction
    CONTRADICTS = "CONTRADICTS"  # Opposes another claim/invariant
    ATTACKS = "ATTACKS"  # Structural invalidation
    INVALIDATES = "INVALIDATES"  # Hard invariant breach


class Coherence(StrEnum):
    COHERENT = "COHERENT"  # Representations form one trustworthy state
    PARTIALLY_COHERENT = "PARTIALLY_COHERENT"  # Non-critical divergences
    DECOHERENT = "DECOHERENT"  # Unreconciled divergence
    RECONCILING = "RECONCILING"  # Reconciler active


class EvidenceStatus(StrEnum):
    ABSENT = "ABSENT"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"


class OperationalLifecycle(StrEnum):
    INITIALIZING = "INITIALIZING"
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    SAFE_HOLD = "SAFE_HOLD"
    QUARANTINED = "QUARANTINED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class StateVector:
    """
    Typed Product State Vector:
    S(e, t) = <P, V, A, C, E, L, tau>
    """

    presence: Presence = Presence.PRESENT
    valence: Valence = Valence.POSITIVE
    anti: Anti = Anti.NONE
    coherence: Coherence = Coherence.COHERENT
    evidence: EvidenceStatus = EvidenceStatus.VERIFIED
    lifecycle: OperationalLifecycle = OperationalLifecycle.NORMAL
    epoch: float = field(default_factory=lambda: datetime.now(UTC).timestamp())
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        """
        Hard invariants dominate scores:
        If anti != NONE or coherence == DECOHERENT or presence == UNKNOWN for mandatory states,
        state is non-conformant.
        """
        if self.anti in (Anti.ATTACKS, Anti.INVALIDATES):
            return False
        if self.coherence == Coherence.DECOHERENT:
            return False
        if self.lifecycle in (OperationalLifecycle.FAILED, OperationalLifecycle.QUARANTINED):
            return False
        return self.valence == Valence.POSITIVE


@dataclass(frozen=True)
class ConformanceTransition:
    """
    Canonical Transition Vector Contract:
    delta(Pe, S0, X, C) = <d, O, S1, E, R>
    """

    disposition: str  # ADMIT, DENY, ESCALATE, SAFE_HOLD, QUARANTINE
    obligations: tuple[str, ...]
    resulting_state: StateVector
    required_evidence: tuple[str, ...]
    recovery_triggers: tuple[str, ...]
