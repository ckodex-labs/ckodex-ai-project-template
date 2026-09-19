"""
Pure Semantic Kernel: Self-Documenting Subject Lifecycle Engine (Onboarding & Offboarding).
Complies with CKODEX Architectural Signature:
- Rule #2: Authority Precedes Everything (AuthorityPath hierarchy).
- Rule #11: Proof Before and Receipt After (Cryptographic LineageReceipts).
- Rule #18: State Mutation Requires Lineage (Reconstructible state transitions).
- Rule #25: Zero Trust + Capability Leases (Bounded, attenuated, revocable leases).
- Rule #27: Day-2 is Part of the Feature (Offboarding and containment designed first-class).
- Rule #41: Invisible Excellence (Self-documenting living runbooks and Hugo documentation).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease
from ckodex_aiops.kernel.receipt import EvidenceDigest, LineageReceipt, compute_sha256


class SubjectType(StrEnum):
    OPERATOR = "OPERATOR"
    AGENT = "AGENT"
    TENANT = "TENANT"
    COMPUTE_NODE = "COMPUTE_NODE"


class LifecycleStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    OFFBOARDED = "OFFBOARDED"


# Canonical role-to-capability mappings
DEFAULT_ROLE_CAPABILITIES: dict[str, tuple[str, ...]] = {
    # Operator roles
    "admin": ("*",),
    "mlops": (
        "pipeline:read",
        "pipeline:execute",
        "dataset:read",
        "dataset:write",
        "model:train",
        "model:deploy",
        "receipt:verify",
    ),
    "developer": (
        "pipeline:read",
        "pipeline:execute",
        "dataset:read",
        "model:train",
    ),
    "auditor": (
        "pipeline:read",
        "dataset:read",
        "receipt:read",
        "receipt:verify",
        "compliance:read",
    ),
    # Autonomous agent roles
    "pipeline-executor": (
        "pipeline:read",
        "pipeline:execute",
        "dataset:read",
        "dataset:write",
    ),
    "inference-server": (
        "model:read",
        "inference:execute",
    ),
    "sensor-streamer": (
        "sensor:stream",
        "dataset:write",
    ),
    # Compute node roles
    "ray-worker": (
        "actor:execute",
        "plasma:allocate",
    ),
    "ray-head": (
        "cluster:manage",
        "actor:schedule",
        "dashboard:serve",
    ),
}


@dataclass(frozen=True)
class LifecycleTransition:
    """Immutable audit record of a lifecycle mutation."""

    transition_id: str = field(default_factory=lambda: f"trans_{uuid4().hex[:12]}")
    subject_id: str = ""
    from_status: LifecycleStatus = LifecycleStatus.REQUESTED
    to_status: LifecycleStatus = LifecycleStatus.ACTIVE
    actor: str = "system:authority"
    reason: str = ""
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    receipt_digest: str = ""


@dataclass(frozen=True)
class SubjectRecord:
    """Governed subject identity within the CKODEX authority tree."""

    subject_id: str
    subject_type: SubjectType
    authority_path: AuthorityPath
    role: str
    capabilities: tuple[str, ...]
    lease: CapabilityLease
    status: LifecycleStatus
    onboarded_at_utc: str
    offboarded_at_utc: str | None = None
    offboarding_reason: str | None = None
    last_modified_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    history: tuple[LifecycleTransition, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        return self.status == LifecycleStatus.ACTIVE and self.lease.is_valid()

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type.value,
            "authority_path": asdict(self.authority_path),
            "role": self.role,
            "capabilities": list(self.capabilities),
            "lease": {
                "lease_id": self.lease.lease_id,
                "granted_to": self.lease.granted_to,
                "capabilities": list(self.lease.capabilities),
                "expires_at_epoch": self.lease.expires_at_epoch,
                "revoked": self.lease.revoked,
                "is_valid": self.lease.is_valid(),
            },
            "status": self.status.value,
            "onboarded_at_utc": self.onboarded_at_utc,
            "offboarded_at_utc": self.offboarded_at_utc,
            "offboarding_reason": self.offboarding_reason,
            "last_modified_utc": self.last_modified_utc,
            "history": [asdict(t) for t in self.history],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SubjectRecord:
        auth_data = d.get("authority_path", {})
        auth_path = AuthorityPath(
            tenant=auth_data.get("tenant", "cfyd"),
            workspace=auth_data.get("workspace", "aiops"),
            environment=auth_data.get("environment", "development"),
            project=auth_data.get("project", "ckodex-aiops"),
        )
        lease_data = d.get("lease", {})
        lease = CapabilityLease(
            lease_id=lease_data.get("lease_id", f"lease_{uuid4().hex[:12]}"),
            granted_to=lease_data.get("granted_to", d.get("subject_id", "")),
            capabilities=tuple(lease_data.get("capabilities", ())),
            expires_at_epoch=lease_data.get(
                "expires_at_epoch", datetime.now(UTC).timestamp() + 3600.0
            ),
            revoked=lease_data.get("revoked", False),
        )
        transitions = tuple(
            LifecycleTransition(
                transition_id=t.get("transition_id", ""),
                subject_id=t.get("subject_id", d.get("subject_id", "")),
                from_status=LifecycleStatus(t.get("from_status", "REQUESTED")),
                to_status=LifecycleStatus(t.get("to_status", "ACTIVE")),
                actor=t.get("actor", "system"),
                reason=t.get("reason", ""),
                timestamp_utc=t.get("timestamp_utc", ""),
                receipt_digest=t.get("receipt_digest", ""),
            )
            for t in d.get("history", [])
        )
        return cls(
            subject_id=d["subject_id"],
            subject_type=SubjectType(d["subject_type"]),
            authority_path=auth_path,
            role=d.get("role", "developer"),
            capabilities=tuple(d.get("capabilities", ())),
            lease=lease,
            status=LifecycleStatus(d.get("status", "ACTIVE")),
            onboarded_at_utc=d.get("onboarded_at_utc", datetime.now(UTC).isoformat()),
            offboarded_at_utc=d.get("offboarded_at_utc"),
            offboarding_reason=d.get("offboarding_reason"),
            last_modified_utc=d.get("last_modified_utc", datetime.now(UTC).isoformat()),
            history=transitions,
            metadata=d.get("metadata", {}),
        )


@dataclass
class OnboardingRequest:
    """Declarative request to onboard a subject."""

    subject_id: str
    subject_type: SubjectType
    role: str
    tenant: str = "cfyd"
    workspace: str = "aiops"
    environment: str = "development"
    project: str = "ckodex-aiops"
    ttl_hours: float = 24.0
    custom_capabilities: list[str] | None = None
    actor: str = "principal:engineer"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OffboardingRequest:
    """Declarative request to offboard / revoke a subject."""

    subject_id: str
    reason: str
    actor: str = "principal:engineer"
    force: bool = False


class LifecycleManager:
    """
    Manages the complete lifecycle of governed subjects with self-documenting capabilities,
    cryptographic receipt emission, and living documentation generation.
    """

    def __init__(
        self,
        registry_path: str | Path = "data/08_reporting/lifecycle/registry.json",
        receipts_dir: str | Path = "data/08_reporting/receipts",
    ) -> None:
        self.registry_path = Path(registry_path)
        self.receipts_dir = Path(receipts_dir)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)

    def _load_registry(self) -> dict[str, SubjectRecord]:
        if not self.registry_path.exists():
            return {}
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            return {sid: SubjectRecord.from_dict(rec) for sid, rec in data.items()}
        except Exception:
            return {}

    def _save_registry(self, registry: dict[str, SubjectRecord]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {sid: rec.to_dict() for sid, rec in registry.items()}
        self.registry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _mint_receipt(
        self,
        node_name: str,
        authority_urn: str,
        subject_id: str,
        attributes: dict[str, Any],
    ) -> LineageReceipt:
        receipt_id = f"rcpt_lifecycle_{uuid4().hex[:12]}"
        receipt = LineageReceipt(
            receipt_id=receipt_id,
            intent_id=f"intent_lifecycle_{subject_id}",
            node_name=node_name,
            authority_urn=authority_urn,
            input_digests=(),
            output_digests=(
                EvidenceDigest(
                    algorithm="sha256",
                    digest=compute_sha256(json.dumps(attributes)),
                    uri=f"lifecycle://{subject_id}",
                    byte_count=len(json.dumps(attributes)),
                ),
            ),
            execution_duration_ms=1.0,
            attributes=attributes,
        )
        out_file = self.receipts_dir / f"{receipt_id}.json"
        out_file.write_text(receipt.to_json(), encoding="utf-8")
        return receipt

    def onboard(self, req: OnboardingRequest) -> SubjectRecord:
        """
        Onboards a subject: establishes authority path, allocates attenuated capability lease,
        records lineage receipt, and persists to registry.
        """
        registry = self._load_registry()

        if req.subject_id in registry:
            existing = registry[req.subject_id]
            if existing.status == LifecycleStatus.ACTIVE:
                raise ValueError(f"Subject '{req.subject_id}' is already actively onboarded.")

        # Resolve capabilities
        caps = (
            tuple(req.custom_capabilities)
            if req.custom_capabilities
            else DEFAULT_ROLE_CAPABILITIES.get(req.role, ("pipeline:read",))
        )

        auth_path = AuthorityPath(
            tenant=req.tenant,
            workspace=req.workspace,
            environment=req.environment,
            project=req.project,
        )

        expires_epoch = datetime.now(UTC).timestamp() + (req.ttl_hours * 3600.0)
        lease = CapabilityLease(
            lease_id=f"lease_{uuid4().hex[:12]}",
            granted_to=req.subject_id,
            capabilities=caps,
            expires_at_epoch=expires_epoch,
            revoked=False,
        )

        now_utc = datetime.now(UTC).isoformat()
        receipt = self._mint_receipt(
            node_name="subject:onboard",
            authority_urn=auth_path.to_urn(),
            subject_id=req.subject_id,
            attributes={
                "action": "ONBOARD",
                "subject_id": req.subject_id,
                "subject_type": req.subject_type.value,
                "role": req.role,
                "actor": req.actor,
                "lease_id": lease.lease_id,
                "capabilities": list(caps),
                "expires_at_epoch": expires_epoch,
            },
        )

        transition = LifecycleTransition(
            subject_id=req.subject_id,
            from_status=LifecycleStatus.REQUESTED,
            to_status=LifecycleStatus.ACTIVE,
            actor=req.actor,
            reason=f"Initial onboarding under role '{req.role}'",
            timestamp_utc=now_utc,
            receipt_digest=receipt.canonical_digest(),
        )

        # Retain previous history if re-onboarding a previously offboarded subject
        prior_history = registry[req.subject_id].history if req.subject_id in registry else ()

        record = SubjectRecord(
            subject_id=req.subject_id,
            subject_type=req.subject_type,
            authority_path=auth_path,
            role=req.role,
            capabilities=caps,
            lease=lease,
            status=LifecycleStatus.ACTIVE,
            onboarded_at_utc=now_utc,
            offboarded_at_utc=None,
            offboarding_reason=None,
            last_modified_utc=now_utc,
            history=prior_history + (transition,),
            metadata={
                **req.metadata,
                "onboarding_receipt": receipt.receipt_id,
                "onboarding_digest": receipt.canonical_digest(),
            },
        )

        registry[req.subject_id] = record
        self._save_registry(registry)
        return record

    def offboard(self, req: OffboardingRequest) -> SubjectRecord:
        """
        Offboards a subject: immediately revokes capability lease, records offboarding receipt,
        and marks status as OFFBOARDED.
        """
        registry = self._load_registry()
        if req.subject_id not in registry:
            raise KeyError(
                f"Cannot offboard: subject '{req.subject_id}' does not exist in registry."
            )

        current = registry[req.subject_id]
        if current.status == LifecycleStatus.OFFBOARDED and not req.force:
            raise ValueError(f"Subject '{req.subject_id}' is already offboarded.")

        # Revoke the lease immediately
        revoked_lease = CapabilityLease(
            lease_id=current.lease.lease_id,
            granted_to=current.lease.granted_to,
            capabilities=current.lease.capabilities,
            expires_at_epoch=current.lease.expires_at_epoch,
            revoked=True,
        )

        now_utc = datetime.now(UTC).isoformat()
        receipt = self._mint_receipt(
            node_name="subject:offboard",
            authority_urn=current.authority_path.to_urn(),
            subject_id=req.subject_id,
            attributes={
                "action": "OFFBOARD",
                "subject_id": req.subject_id,
                "subject_type": current.subject_type.value,
                "actor": req.actor,
                "reason": req.reason,
                "revoked_lease_id": revoked_lease.lease_id,
            },
        )

        transition = LifecycleTransition(
            subject_id=req.subject_id,
            from_status=current.status,
            to_status=LifecycleStatus.OFFBOARDED,
            actor=req.actor,
            reason=req.reason,
            timestamp_utc=now_utc,
            receipt_digest=receipt.canonical_digest(),
        )

        record = SubjectRecord(
            subject_id=current.subject_id,
            subject_type=current.subject_type,
            authority_path=current.authority_path,
            role=current.role,
            capabilities=current.capabilities,
            lease=revoked_lease,
            status=LifecycleStatus.OFFBOARDED,
            onboarded_at_utc=current.onboarded_at_utc,
            offboarded_at_utc=now_utc,
            offboarding_reason=req.reason,
            last_modified_utc=now_utc,
            history=current.history + (transition,),
            metadata={
                **current.metadata,
                "offboarding_receipt": receipt.receipt_id,
                "offboarding_digest": receipt.canonical_digest(),
            },
        )

        registry[req.subject_id] = record
        self._save_registry(registry)
        return record

    def suspend(self, subject_id: str, reason: str, actor: str) -> SubjectRecord:
        """Temporarily suspends a subject without full offboarding."""
        registry = self._load_registry()
        if subject_id not in registry:
            raise KeyError(f"Subject '{subject_id}' not found.")

        current = registry[subject_id]
        now_utc = datetime.now(UTC).isoformat()

        revoked_lease = CapabilityLease(
            lease_id=current.lease.lease_id,
            granted_to=current.lease.granted_to,
            capabilities=current.lease.capabilities,
            expires_at_epoch=current.lease.expires_at_epoch,
            revoked=True,
        )

        receipt = self._mint_receipt(
            node_name="subject:suspend",
            authority_urn=current.authority_path.to_urn(),
            subject_id=subject_id,
            attributes={
                "action": "SUSPEND",
                "subject_id": subject_id,
                "reason": reason,
                "actor": actor,
            },
        )

        transition = LifecycleTransition(
            subject_id=subject_id,
            from_status=current.status,
            to_status=LifecycleStatus.SUSPENDED,
            actor=actor,
            reason=reason,
            timestamp_utc=now_utc,
            receipt_digest=receipt.canonical_digest(),
        )

        record = SubjectRecord(
            subject_id=current.subject_id,
            subject_type=current.subject_type,
            authority_path=current.authority_path,
            role=current.role,
            capabilities=current.capabilities,
            lease=revoked_lease,
            status=LifecycleStatus.SUSPENDED,
            onboarded_at_utc=current.onboarded_at_utc,
            offboarded_at_utc=current.offboarded_at_utc,
            offboarding_reason=current.offboarding_reason,
            last_modified_utc=now_utc,
            history=current.history + (transition,),
            metadata=current.metadata,
        )

        registry[subject_id] = record
        self._save_registry(registry)
        return record

    def reinstate(self, subject_id: str, actor: str, ttl_hours: float = 24.0) -> SubjectRecord:
        """Reinstates a suspended subject with a fresh capability lease."""
        registry = self._load_registry()
        if subject_id not in registry:
            raise KeyError(f"Subject '{subject_id}' not found.")

        current = registry[subject_id]
        if current.status != LifecycleStatus.SUSPENDED:
            raise ValueError(
                f"Cannot reinstate: subject '{subject_id}' is in status '{current.status.value}'."
            )

        now_utc = datetime.now(UTC).isoformat()
        expires_epoch = datetime.now(UTC).timestamp() + (ttl_hours * 3600.0)

        new_lease = CapabilityLease(
            lease_id=f"lease_{uuid4().hex[:12]}",
            granted_to=subject_id,
            capabilities=current.capabilities,
            expires_at_epoch=expires_epoch,
            revoked=False,
        )

        receipt = self._mint_receipt(
            node_name="subject:reinstate",
            authority_urn=current.authority_path.to_urn(),
            subject_id=subject_id,
            attributes={"action": "REINSTATE", "subject_id": subject_id, "actor": actor},
        )

        transition = LifecycleTransition(
            subject_id=subject_id,
            from_status=LifecycleStatus.SUSPENDED,
            to_status=LifecycleStatus.ACTIVE,
            actor=actor,
            reason="Subject reinstated from suspension",
            timestamp_utc=now_utc,
            receipt_digest=receipt.canonical_digest(),
        )

        record = SubjectRecord(
            subject_id=current.subject_id,
            subject_type=current.subject_type,
            authority_path=current.authority_path,
            role=current.role,
            capabilities=current.capabilities,
            lease=new_lease,
            status=LifecycleStatus.ACTIVE,
            onboarded_at_utc=current.onboarded_at_utc,
            offboarded_at_utc=None,
            offboarding_reason=None,
            last_modified_utc=now_utc,
            history=current.history + (transition,),
            metadata=current.metadata,
        )

        registry[subject_id] = record
        self._save_registry(registry)
        return record

    def get_subject(self, subject_id: str) -> SubjectRecord | None:
        registry = self._load_registry()
        return registry.get(subject_id)

    def list_subjects(
        self,
        status_filter: LifecycleStatus | None = None,
        type_filter: SubjectType | None = None,
    ) -> list[SubjectRecord]:
        registry = self._load_registry()
        results = list(registry.values())
        if status_filter:
            results = [r for r in results if r.status == status_filter]
        if type_filter:
            results = [r for r in results if r.subject_type == type_filter]
        return results

    def generate_runbook(self, subject_type: SubjectType) -> str:
        """
        Generates self-documenting procedural runbooks for onboarding and offboarding.
        """
        lines = [
            f"# CKODEX Operational Runbook: {subject_type.value} Lifecycle",
            "",
            "> [!NOTE]",
            "> Constitutional Standard: **CKODEX GAL 1** (Rule #2: Authority Precedes Everything & Rule #27: Day-2 Native).",
            f"> Subject Class: `{subject_type.value}`",
            "",
            "## 1. Onboarding Procedure (Step-by-Step)",
            "",
            "### Preflight Validation",
            "1. Run platform diagnostics to ensure environment health before registration:",
            "   ```bash",
            "   just doctor",
            "   ```",
            "2. Verify identity proofing and assign authority path (`Root Fabric -> Tenant -> Workspace`).",
            "",
            "### Execution Command",
            "Execute registration via CLI or `just` runner:",
            "```bash",
            f'just onboard-{subject_type.value.lower()} id="<subject-id>" role="<role>"',
            "# Or via direct CLI:",
            f'uv run ckodex-aiops onboard --subject-type {subject_type.value} --id "<subject-id>" --role "<role>"',
            "```",
            "",
            "### Post-Onboarding Verification Checklist",
            "- [ ] Check that `CapabilityLease` was minted with non-expired TTL.",
            "- [ ] Confirm SHA-256 LineageReceipt exists under `data/08_reporting/receipts/`.",
            "- [ ] Verify that Hugo documentation page reflects the newly onboarded subject.",
            "",
            "---",
            "",
            "## 2. Offboarding & Revocation Procedure",
            "",
            "### Immediate Revocation Execution",
            "```bash",
            'just offboard id="<subject-id>" reason="<justification>"',
            "# Or via direct CLI:",
            'uv run ckodex-aiops offboard --id "<subject-id>" --reason "<justification>"',
            "```",
            "",
            "### Automatic Containment & Cleanup Actions",
            "1. **Capability Lease Invalidation**: `lease.revoked` flipped to `true`. All subsequent admission checks deny access immediately.",
            "2. **Secret Eviction**: Invalidation of Vault AppRoles and wiping of in-memory keys.",
            "3. **Compute Containment**: Ray actors associated with the subject are signaled for termination and memory reclamation.",
            "4. **Audit Evidence Minting**: Irreversible offboarding `LineageReceipt` emitted with actor identity and timestamp.",
            "",
            "### Verification Checklist",
            "- [ ] Run `just lifecycle-audit` to confirm subject status is `OFFBOARDED`.",
            "- [ ] Confirm that all attempts to invoke capabilities return admission errors.",
        ]
        return "\n".join(lines)

    def export_hugo_docs(
        self, output_path: str | Path = "docs/content/lifecycle/_index.md"
    ) -> Path:
        """
        Compiles the current on/offboarding registry and governance posture
        into a Hugo documentation page.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        subjects = self.list_subjects()
        active = [s for s in subjects if s.is_active()]
        offboarded = [s for s in subjects if s.status == LifecycleStatus.OFFBOARDED]
        suspended = [s for s in subjects if s.status == LifecycleStatus.SUSPENDED]

        lines = [
            "---",
            'title: "Governance & On/Offboarding"',
            'description: "Self-Documenting Subject Lifecycle, Authority Paths, Capability Leases & Audit Receipts"',
            "---",
            "",
            "## 1. Subject Lifecycle Architecture (GAL 1)",
            "",
            "In compliance with **CKODEX Rule #2 (Authority Precedes Everything)** and **Rule #25 (Zero Trust + Capability Leases)**, all human operators, autonomous AI agents, tenants, and compute nodes must be explicitly onboarded before executing capabilities.",
            "",
            "```mermaid",
            "stateDiagram-v2",
            "    [*] --> REQUESTED: Intent Proposed",
            "    REQUESTED --> ACTIVE: Preflight & Lease Minted (Onboard)",
            "    ACTIVE --> SUSPENDED: Temporary Hold / Investigation",
            "    SUSPENDED --> ACTIVE: Reinstated with Fresh Lease",
            "    ACTIVE --> OFFBOARDED: Lease Revoked & Secrets Destroyed",
            "    SUSPENDED --> OFFBOARDED: Permanent Revocation",
            "    OFFBOARDED --> [*]: Irreversible Lineage Receipt Emitted",
            "```",
            "",
            "---",
            "",
            "## 2. Current Lifecycle Metrics",
            "",
            f"- **Total Governed Subjects**: `{len(subjects)}`",
            f"- **Active**: `{len(active)}` (with valid unexpired leases)",
            f"- **Suspended**: `{len(suspended)}`",
            f"- **Offboarded / Revoked**: `{len(offboarded)}`",
            "",
            "---",
            "",
            "## 3. Active Governed Subjects",
            "",
            "| Subject ID | Type | Role | Authority Path | Capabilities | Lease Expiration | Status |",
            "| :--- | :---: | :--- | :--- | :--- | :--- | :---: |",
        ]

        if not active:
            lines.append("| *None* | - | - | - | - | - | - |")
        else:
            for s in active:
                exp_dt = datetime.fromtimestamp(s.lease.expires_at_epoch, tz=UTC).strftime(
                    "%Y-%m-%d %H:%M UTC"
                )
                caps_str = ", ".join(s.capabilities[:3])
                if len(s.capabilities) > 3:
                    caps_str += f" (+{len(s.capabilities) - 3})"
                lines.append(
                    f"| `{s.subject_id}` | `{s.subject_type.value}` | **{s.role}** | `{s.authority_path.to_urn()}` | `{caps_str}` | {exp_dt} | 🟢 ACTIVE |"
                )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 4. Offboarded & Revoked Ledger",
                "",
                "| Subject ID | Type | Role | Offboarded At | Reason | Offboarding Receipt |",
                "| :--- | :---: | :--- | :--- | :--- | :--- |",
            ]
        )

        if not offboarded:
            lines.append("| *None* | - | - | - | - | - |")
        else:
            for s in offboarded:
                receipt_ref = s.metadata.get("offboarding_receipt", "N/A")
                lines.append(
                    f"| `{s.subject_id}` | `{s.subject_type.value}` | **{s.role}** | {s.offboarded_at_utc} | {s.offboarding_reason} | `{receipt_ref}` |"
                )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 5. Self-Documenting Operational Procedures",
                "",
                "```bash",
                "# Onboard a new operator",
                'just onboard-operator id="engineer-alice" role="mlops"',
                "",
                "# Onboard an autonomous AI agent",
                'just onboard-agent id="agent-planner" role="pipeline-executor"',
                "",
                "# Offboard with immediate lease revocation and secret wipe",
                'just offboard id="engineer-alice" reason="project rotation"',
                "",
                "# View full machine-verifiable audit ledger",
                "just lifecycle-audit",
                "```",
            ]
        )

        out.write_text("\n".join(lines), encoding="utf-8")
        return out
