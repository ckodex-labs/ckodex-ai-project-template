"""
Pure Semantic Kernel: Intent & Capability Leases.
Complies with CKODEX Architectural Signature: Authority-born, Intent-native.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class IntentLifecycle(StrEnum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    ADMITTED = "ADMITTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class AuthorityPath:
    """
    Standing authority hierarchy:
    Root Fabric -> Tenant -> Namespace -> Workspace -> Plane -> Environment -> Project -> Resource
    """

    tenant: str
    workspace: str
    environment: str = "development"
    project: str = "ckodex-aiops"

    def to_urn(self) -> str:
        return f"urn:ckodex:{self.tenant}:{self.workspace}:{self.environment}:{self.project}"


@dataclass(frozen=True)
class CapabilityLease:
    """
    Bounded, attenuated execution lease. Authority precedes execution.
    """

    lease_id: str = field(default_factory=lambda: f"lease_{uuid4().hex[:12]}")
    granted_to: str = "system:aiops-runner"
    capabilities: tuple[str, ...] = ("pipeline:read", "pipeline:execute", "dataset:write")
    expires_at_epoch: float = field(default_factory=lambda: datetime.now(UTC).timestamp() + 3600.0)
    revoked: bool = False

    def is_valid(self) -> bool:
        if self.revoked:
            return False
        return datetime.now(UTC).timestamp() < self.expires_at_epoch

    def permits(self, capability: str) -> bool:
        return self.is_valid() and capability in self.capabilities


@dataclass(frozen=True)
class IntentEnvelope:
    """
    Canonical unit of work across all pipelines, models, and operations.
    """

    intent_id: str = field(default_factory=lambda: f"intent_{uuid4().hex[:12]}")
    actor: str = "principal:engineer"
    authority: AuthorityPath = field(
        default_factory=lambda: AuthorityPath(tenant="cfyd", workspace="aiops")
    )
    requested_capability: str = "pipeline:execute"
    lease: CapabilityLease = field(default_factory=CapabilityLease)
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    lifecycle: IntentLifecycle = IntentLifecycle.PROPOSED

    def transition(self, new_lifecycle: IntentLifecycle) -> IntentEnvelope:
        return IntentEnvelope(
            intent_id=self.intent_id,
            actor=self.actor,
            authority=self.authority,
            requested_capability=self.requested_capability,
            lease=self.lease,
            payload=self.payload,
            created_at_utc=self.created_at_utc,
            lifecycle=new_lifecycle,
        )
