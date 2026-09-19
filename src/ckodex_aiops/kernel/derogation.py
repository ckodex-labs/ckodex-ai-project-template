"""
Pure Semantic Kernel: Explicit Derogation & Accepted Risk Engine (Rule #23).
Accepted risk does not rewrite history.
A derogation explicitly binds:
- failed requirement
- scope
- authority
- justification
- compensating controls
- evidence digest
- expiry
- re-evaluation trigger

The underlying StateVector remains truthful (valence/anti is not falsified).
Never convert FAIL into PASS because someone accepted the risk.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ckodex_aiops.kernel.intent import AuthorityPath
from ckodex_aiops.kernel.receipt import compute_sha256


@dataclass(frozen=True)
class DerogationRecord:
    """
    Explicit, auditable record of an approved risk derogation (Rule #23).
    """

    derogation_id: str
    failed_requirement: str
    scope: str
    authority_urn: str
    approver: str
    justification: str
    compensating_controls: tuple[str, ...]
    evidence_digest: str
    granted_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at_epoch: float = field(
        default_factory=lambda: datetime.now(UTC).timestamp() + 86400.0 * 7
    )  # 7-day default
    re_evaluation_trigger: str = "SCHEDULED_WEEKLY_REVIEW_OR_INCIDENT"
    active: bool = True

    def is_valid(self) -> bool:
        """A derogation is valid only if active and before expiration."""
        if not self.active:
            return False
        return datetime.now(UTC).timestamp() < self.expires_at_epoch

    def canonical_digest(self) -> str:
        payload = {
            "derogation_id": self.derogation_id,
            "failed_requirement": self.failed_requirement,
            "scope": self.scope,
            "authority_urn": self.authority_urn,
            "approver": self.approver,
            "justification": self.justification,
            "compensating_controls": list(self.compensating_controls),
            "granted_at_utc": self.granted_at_utc,
            "expires_at_epoch": self.expires_at_epoch,
            "re_evaluation_trigger": self.re_evaluation_trigger,
        }
        return compute_sha256(json.dumps(payload, sort_keys=True))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class DerogationRegistry:
    """
    Persistent, content-addressed registry for risk derogations.
    Preserves audit trail under data/08_reporting/derogations/.
    """

    def __init__(self, storage_dir: str | Path = "data/08_reporting/derogations") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_derogation(
        self,
        failed_requirement: str,
        scope: str,
        approver: str,
        justification: str,
        compensating_controls: list[str] | tuple[str, ...],
        evidence_digest: str,
        authority: AuthorityPath | None = None,
        duration_days: float = 7.0,
        re_evaluation_trigger: str = "SCHEDULED_REVIEW_OR_INCIDENT",
    ) -> DerogationRecord:
        auth_urn = (
            authority.to_urn() if authority else "urn:ckodex:cfyd:aiops:development:ckodex-aiops"
        )
        derogation_id = f"derog_{uuid4().hex[:12]}"
        now = datetime.now(UTC)
        expires_epoch = now.timestamp() + (duration_days * 86400.0)

        record = DerogationRecord(
            derogation_id=derogation_id,
            failed_requirement=failed_requirement,
            scope=scope,
            authority_urn=auth_urn,
            approver=approver,
            justification=justification,
            compensating_controls=tuple(compensating_controls),
            evidence_digest=evidence_digest,
            granted_at_utc=now.isoformat(),
            expires_at_epoch=expires_epoch,
            re_evaluation_trigger=re_evaluation_trigger,
            active=True,
        )

        record_file = self.storage_dir / f"{derogation_id}.json"
        record_file.write_text(record.to_json(), encoding="utf-8")
        return record

    def get_derogation(self, derogation_id: str) -> DerogationRecord | None:
        record_file = self.storage_dir / f"{derogation_id}.json"
        if not record_file.exists():
            return None
        data = json.loads(record_file.read_text(encoding="utf-8"))
        return DerogationRecord(
            derogation_id=data["derogation_id"],
            failed_requirement=data["failed_requirement"],
            scope=data["scope"],
            authority_urn=data["authority_urn"],
            approver=data["approver"],
            justification=data["justification"],
            compensating_controls=tuple(data.get("compensating_controls", [])),
            evidence_digest=data["evidence_digest"],
            granted_at_utc=data["granted_at_utc"],
            expires_at_epoch=data["expires_at_epoch"],
            re_evaluation_trigger=data["re_evaluation_trigger"],
            active=data.get("active", True),
        )

    def list_derogations(self, active_only: bool = True) -> list[DerogationRecord]:
        records: list[DerogationRecord] = []
        for file in sorted(self.storage_dir.glob("derog_*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                rec = DerogationRecord(
                    derogation_id=data["derogation_id"],
                    failed_requirement=data["failed_requirement"],
                    scope=data["scope"],
                    authority_urn=data["authority_urn"],
                    approver=data["approver"],
                    justification=data["justification"],
                    compensating_controls=tuple(data.get("compensating_controls", [])),
                    evidence_digest=data["evidence_digest"],
                    granted_at_utc=data["granted_at_utc"],
                    expires_at_epoch=data["expires_at_epoch"],
                    re_evaluation_trigger=data["re_evaluation_trigger"],
                    active=data.get("active", True),
                )
                if not active_only or rec.is_valid():
                    records.append(rec)
            except Exception:
                continue
        return records

    def revoke_derogation(self, derogation_id: str, reason: str) -> DerogationRecord:
        record = self.get_derogation(derogation_id)
        if not record:
            raise KeyError(f"Derogation '{derogation_id}' not found.")

        updated = DerogationRecord(
            derogation_id=record.derogation_id,
            failed_requirement=record.failed_requirement,
            scope=record.scope,
            authority_urn=record.authority_urn,
            approver=record.approver,
            justification=f"{record.justification} [REVOKED: {reason}]",
            compensating_controls=record.compensating_controls,
            evidence_digest=record.evidence_digest,
            granted_at_utc=record.granted_at_utc,
            expires_at_epoch=datetime.now(UTC).timestamp() - 1.0,
            re_evaluation_trigger="EXPLICITLY_REVOKED",
            active=False,
        )
        record_file = self.storage_dir / f"{derogation_id}.json"
        record_file.write_text(updated.to_json(), encoding="utf-8")
        return updated

    def audit_derogations(self) -> dict[str, Any]:
        all_records = self.list_derogations(active_only=False)
        active_records = [r for r in all_records if r.is_valid()]
        expired_records = [r for r in all_records if not r.is_valid()]

        return {
            "total_derogations": len(all_records),
            "active_derogations": len(active_records),
            "expired_or_revoked_derogations": len(expired_records),
            "active_ids": [r.derogation_id for r in active_records],
            "records": [r.to_dict() for r in active_records],
        }
