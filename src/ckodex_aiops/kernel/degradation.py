"""
Pure Semantic Kernel: Explicit Runtime Modes & Degraded Mode Contracts (Rules #29, #30).
Governs operational modes: NORMAL, DEGRADED, SAFE_HOLD, QUARANTINED, RECOVERING, FAILED.
Enforces that degraded operation adheres to an explicit contractual boundary:
- trigger
- residual capability
- prohibited capability
- freshness tolerance
- security guarantees
- data/scientific integrity guarantees
- recovery criteria
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from ckodex_aiops.kernel.receipt import compute_sha256
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    OperationalLifecycle,
    StateVector,
    Valence,
)


class RuntimeMode(StrEnum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    SAFE_HOLD = "SAFE_HOLD"
    QUARANTINED = "QUARANTINED"
    RECOVERING = "RECOVERING"
    FAILED = "FAILED"


class ContainmentScope(StrEnum):
    NONE = "NONE"
    LOCAL_ONLY = "LOCAL_ONLY"
    PROOF_ONLY = "PROOF_ONLY"
    READ_ONLY = "READ_ONLY"
    BLOCKED_WRITES = "BLOCKED_WRITES"
    QUARANTINE = "QUARANTINE"
    EMERGENCY_REVOKE = "EMERGENCY_REVOKE"


@dataclass(frozen=True)
class DegradedModeContract:
    """
    Contract governing degraded operational behavior (Rule #30).
    Never silently weakens security or data integrity invariants to preserve availability.
    """

    contract_id: str
    name: str
    trigger_condition: str
    containment: ContainmentScope
    residual_capabilities: tuple[str, ...]
    prohibited_capabilities: tuple[str, ...]
    freshness_tolerance_seconds: float
    security_guarantees: tuple[str, ...]
    data_integrity_guarantees: tuple[str, ...]
    recovery_criteria: tuple[str, ...]
    max_exposure_window_seconds: float = 3600.0

    def permits(self, capability: str) -> bool:
        """Determines if a requested capability is permissible under this contract."""
        if capability in self.prohibited_capabilities:
            return False
        return capability in self.residual_capabilities

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DegradationReceipt:
    """Cryptographic evidence of a runtime mode transition into degraded state."""

    receipt_id: str
    previous_mode: RuntimeMode
    current_mode: RuntimeMode
    contract_id: str
    trigger_reason: str
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    digest: str = ""

    def canonical_digest(self) -> str:
        payload = {
            "receipt_id": self.receipt_id,
            "previous_mode": self.previous_mode,
            "current_mode": self.current_mode,
            "contract_id": self.contract_id,
            "trigger_reason": self.trigger_reason,
            "timestamp_utc": self.timestamp_utc,
        }
        return compute_sha256(json.dumps(payload, sort_keys=True))


class DegradationManager:
    """
    Manages degraded mode contracts and evaluates state vectors to transition modes safely.
    """

    def __init__(self) -> None:
        self._contracts: dict[str, DegradedModeContract] = {}
        self._register_default_contracts()

    def _register_default_contracts(self) -> None:
        # Default 1: Read-only cache serving during model drift or training interruption
        self.register_contract(
            DegradedModeContract(
                contract_id="dmc-cache-serving",
                name="Read-Only Cache Serving",
                trigger_condition="Model drift detected or inference worker instability",
                containment=ContainmentScope.READ_ONLY,
                residual_capabilities=("dataset:read", "model:infer_cached", "telemetry:emit"),
                prohibited_capabilities=("model:train", "dataset:write", "weights:update"),
                freshness_tolerance_seconds=1800.0,
                security_guarantees=("Immutable read isolation", "Zero credential escalation"),
                data_integrity_guarantees=("No corrupt checkpoints written to storage",),
                recovery_criteria=(
                    "Reconciler confirms model weights SHA-256 match baseline",
                    "Drift PSI < 0.10",
                ),
                max_exposure_window_seconds=3600.0,
            )
        )

        # Default 2: Proof-only validation when remote network / KMS is unreachable
        self.register_contract(
            DegradedModeContract(
                contract_id="dmc-proof-only",
                name="Proof-Only Offline Validation",
                trigger_condition="Air-gap mode or remote secrets manager unreachable",
                containment=ContainmentScope.PROOF_ONLY,
                residual_capabilities=("receipt:verify", "conformance:evaluate", "doctor:diagnose"),
                prohibited_capabilities=("model:deploy", "cloud:sync", "network:egress"),
                freshness_tolerance_seconds=86400.0,
                security_guarantees=("Strict local execution", "Zero network egress"),
                data_integrity_guarantees=(
                    "All disk hashes cryptographically verified against receipts",
                ),
                recovery_criteria=("Connectivity restored and OIDC workload token refreshed",),
                max_exposure_window_seconds=86400.0,
            )
        )

        # Default 3: Safe Hold during Anti-invariant violation or decoherence
        self.register_contract(
            DegradedModeContract(
                contract_id="dmc-safe-hold",
                name="Containment Safe Hold",
                trigger_condition="Anti-invariant contradiction or decoherent state vector",
                containment=ContainmentScope.BLOCKED_WRITES,
                residual_capabilities=("doctor:diagnose", "telemetry:emit", "receipt:audit"),
                prohibited_capabilities=(
                    "pipeline:execute",
                    "dataset:write",
                    "model:train",
                    "model:infer",
                ),
                freshness_tolerance_seconds=300.0,
                security_guarantees=("All mutative leases revoked", "Egress locked"),
                data_integrity_guarantees=("Complete freeze on dataset modifications",),
                recovery_criteria=("Human operator or automated reconciler clears contradiction",),
                max_exposure_window_seconds=1800.0,
            )
        )

    def register_contract(self, contract: DegradedModeContract) -> None:
        self._contracts[contract.contract_id] = contract

    def get_contract(self, contract_id: str) -> DegradedModeContract | None:
        return self._contracts.get(contract_id)

    def list_contracts(self) -> list[DegradedModeContract]:
        return list(self._contracts.values())

    def evaluate_vector(
        self, current_vector: StateVector, current_mode: RuntimeMode = RuntimeMode.NORMAL
    ) -> tuple[RuntimeMode, DegradedModeContract | None, DegradationReceipt | None]:
        """
        Evaluates a StateVector to determine whether a degraded mode transition is mandatory.
        Rule #22: Hard invariants dominate scores.
        """
        # Anti invariant violation requires immediate SAFE_HOLD or QUARANTINED
        if current_vector.anti in (Anti.ATTACKS, Anti.INVALIDATES):
            target_mode = RuntimeMode.SAFE_HOLD
            contract = self.get_contract("dmc-safe-hold")
            receipt = DegradationReceipt(
                receipt_id=f"deg_{uuid4().hex[:12]}",
                previous_mode=current_mode,
                current_mode=target_mode,
                contract_id=contract.contract_id if contract else "none",
                trigger_reason=f"Anti-invariant violation detected: {current_vector.anti.value}",
            )
            return target_mode, contract, receipt

        # Decoherent state requires SAFE_HOLD
        if current_vector.coherence == Coherence.DECOHERENT:
            target_mode = RuntimeMode.SAFE_HOLD
            contract = self.get_contract("dmc-safe-hold")
            receipt = DegradationReceipt(
                receipt_id=f"deg_{uuid4().hex[:12]}",
                previous_mode=current_mode,
                current_mode=target_mode,
                contract_id=contract.contract_id if contract else "none",
                trigger_reason="State vector coherence is DECOHERENT",
            )
            return target_mode, contract, receipt

        # Adverse valence or degraded lifecycle triggers DEGRADED mode
        if (
            current_vector.valence == Valence.NEGATIVE
            or current_vector.lifecycle == OperationalLifecycle.DEGRADED
        ):
            target_mode = RuntimeMode.DEGRADED
            contract = self.get_contract("dmc-cache-serving")
            receipt = DegradationReceipt(
                receipt_id=f"deg_{uuid4().hex[:12]}",
                previous_mode=current_mode,
                current_mode=target_mode,
                contract_id=contract.contract_id if contract else "none",
                trigger_reason="Adverse valence or degraded lifecycle observed",
            )
            return target_mode, contract, receipt

        # Normal operation
        return RuntimeMode.NORMAL, None, None
