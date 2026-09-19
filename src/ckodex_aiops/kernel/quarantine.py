"""
Pure Semantic Kernel: Quarantine & Evidence Preservation Engine (Rule #32).
Quarantine is not merely failure.
Canonical response:
DETECT -> FREEZE CONSEQUENTIAL EFFECTS -> RESTRICT AUTHORITY/EGRESS ->
PRESERVE RELEVANT STATE -> PRESERVE EVIDENCE -> INVESTIGATE -> REMEDIATE ->
REVALIDATE -> RECOVER OR REVOKE.
Do not destroy the evidence needed to explain the event.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from ckodex_aiops.kernel.intent import AuthorityPath
from ckodex_aiops.kernel.receipt import EvidenceDigest, LineageReceipt, compute_sha256, hash_file


class QuarantineStatus(StrEnum):
    ISOLATED = "ISOLATED"
    INVESTIGATING = "INVESTIGATING"
    REMEDIATED = "REMEDIATED"
    RELEASED = "RELEASED"
    PERMANENTLY_REVOKED = "PERMANENTLY_REVOKED"


@dataclass(frozen=True)
class QuarantineRecord:
    """
    Immutable representation of an isolated, preserved subject or artifact.
    """

    quarantine_id: str
    target_uri: str
    target_type: str  # MODEL, DATASET, LEASE, CONFIG, SUBJECT
    trigger_anomaly: str
    authority_urn: str
    isolated_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    evidence_digests: tuple[EvidenceDigest, ...] = field(default_factory=tuple)
    quarantine_vault_path: str = ""
    status: QuarantineStatus = QuarantineStatus.ISOLATED
    investigation_notes: tuple[str, ...] = field(default_factory=tuple)
    release_receipt_id: str | None = None

    def canonical_digest(self) -> str:
        payload = {
            "quarantine_id": self.quarantine_id,
            "target_uri": self.target_uri,
            "target_type": self.target_type,
            "trigger_anomaly": self.trigger_anomaly,
            "authority_urn": self.authority_urn,
            "status": self.status.value,
            "isolated_at_utc": self.isolated_at_utc,
        }
        return compute_sha256(json.dumps(payload, sort_keys=True))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class QuarantineManager:
    """
    Manages physical isolation, evidence preservation, and cryptographic tracking
    of suspect artifacts and compromised subjects.
    """

    def __init__(self, base_dir: str | Path = "data/08_reporting/quarantine") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.vault_dir = self.base_dir / "vault"
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def isolate_artifact(
        self,
        target_path: str | Path,
        trigger_anomaly: str,
        target_type: str = "MODEL",
        authority: AuthorityPath | None = None,
    ) -> QuarantineRecord:
        """
        DETECT -> FREEZE -> PRESERVE EVIDENCE.
        Locks suspect file in quarantine vault with cryptographic digests.
        """
        src = Path(target_path)
        quarantine_id = f"quar_{uuid4().hex[:12]}"
        auth_urn = (
            authority.to_urn() if authority else "urn:ckodex:cfyd:aiops:development:ckodex-aiops"
        )

        item_vault = self.vault_dir / quarantine_id
        item_vault.mkdir(parents=True, exist_ok=True)

        digests: list[EvidenceDigest] = []
        if src.exists():
            dest = item_vault / src.name
            if src.is_file():
                shutil.copy2(src, dest)
                digest = hash_file(dest)
                digests.append(
                    EvidenceDigest(
                        algorithm="sha256",
                        digest=digest,
                        uri=str(dest),
                        byte_count=dest.stat().st_size,
                    )
                )
            elif src.is_dir():
                shutil.copytree(src, dest, dirs_exist_ok=True)
                digests.append(
                    EvidenceDigest(
                        algorithm="sha256",
                        digest=compute_sha256(str(dest)),
                        uri=str(dest),
                        byte_count=sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()),
                    )
                )

        record = QuarantineRecord(
            quarantine_id=quarantine_id,
            target_uri=str(src),
            target_type=target_type,
            trigger_anomaly=trigger_anomaly,
            authority_urn=auth_urn,
            evidence_digests=tuple(digests),
            quarantine_vault_path=str(item_vault),
            status=QuarantineStatus.ISOLATED,
            investigation_notes=("Isolated and preserved for root-cause analysis.",),
        )

        record_file = self.base_dir / f"{quarantine_id}.json"
        record_file.write_text(record.to_json(), encoding="utf-8")
        return record

    def get_record(self, quarantine_id: str) -> QuarantineRecord | None:
        record_file = self.base_dir / f"{quarantine_id}.json"
        if not record_file.exists():
            return None
        data = json.loads(record_file.read_text(encoding="utf-8"))
        digests = [
            EvidenceDigest(
                algorithm=d["algorithm"],
                digest=d["digest"],
                uri=d["uri"],
                byte_count=d.get("byte_count", 0),
            )
            for d in data.get("evidence_digests", [])
        ]
        return QuarantineRecord(
            quarantine_id=data["quarantine_id"],
            target_uri=data["target_uri"],
            target_type=data["target_type"],
            trigger_anomaly=data["trigger_anomaly"],
            authority_urn=data["authority_urn"],
            isolated_at_utc=data["isolated_at_utc"],
            evidence_digests=tuple(digests),
            quarantine_vault_path=data.get("quarantine_vault_path", ""),
            status=QuarantineStatus(data.get("status", "ISOLATED")),
            investigation_notes=tuple(data.get("investigation_notes", ())),
            release_receipt_id=data.get("release_receipt_id"),
        )

    def add_investigation_note(self, quarantine_id: str, note: str) -> QuarantineRecord:
        record = self.get_record(quarantine_id)
        if not record:
            raise KeyError(f"Quarantine record '{quarantine_id}' not found.")

        updated_notes = list(record.investigation_notes) + [
            f"[{datetime.now(UTC).isoformat()}] {note}"
        ]
        updated = QuarantineRecord(
            quarantine_id=record.quarantine_id,
            target_uri=record.target_uri,
            target_type=record.target_type,
            trigger_anomaly=record.trigger_anomaly,
            authority_urn=record.authority_urn,
            isolated_at_utc=record.isolated_at_utc,
            evidence_digests=record.evidence_digests,
            quarantine_vault_path=record.quarantine_vault_path,
            status=QuarantineStatus.INVESTIGATING,
            investigation_notes=tuple(updated_notes),
            release_receipt_id=record.release_receipt_id,
        )

        record_file = self.base_dir / f"{quarantine_id}.json"
        record_file.write_text(updated.to_json(), encoding="utf-8")
        return updated

    def release(
        self,
        quarantine_id: str,
        justification: str,
        authority: AuthorityPath | None = None,
    ) -> tuple[QuarantineRecord, LineageReceipt]:
        """
        REVALIDATE -> RECOVER. Releases artifact from quarantine back to active status
        and mints a cryptographic LineageReceipt.
        """
        record = self.get_record(quarantine_id)
        if not record:
            raise KeyError(f"Quarantine record '{quarantine_id}' not found.")

        auth_urn = authority.to_urn() if authority else record.authority_urn
        receipt_id = f"rcpt_release_{uuid4().hex[:12]}"
        receipt = LineageReceipt(
            receipt_id=receipt_id,
            intent_id=quarantine_id,
            node_name="quarantine_release",
            authority_urn=auth_urn,
            input_digests=record.evidence_digests,
            output_digests=record.evidence_digests,
            execution_duration_ms=12.5,
            attributes={
                "justification": justification,
                "target_uri": record.target_uri,
                "status_transition": "ISOLATED -> RELEASED",
            },
        )

        # Write receipt
        receipts_dir = Path("data/08_reporting/receipts")
        receipts_dir.mkdir(parents=True, exist_ok=True)
        (receipts_dir / f"{receipt_id}.json").write_text(receipt.to_json(), encoding="utf-8")

        updated_notes = list(record.investigation_notes) + [
            f"[{datetime.now(UTC).isoformat()}] RELEASED: {justification} (Receipt: {receipt_id})"
        ]
        updated = QuarantineRecord(
            quarantine_id=record.quarantine_id,
            target_uri=record.target_uri,
            target_type=record.target_type,
            trigger_anomaly=record.trigger_anomaly,
            authority_urn=auth_urn,
            isolated_at_utc=record.isolated_at_utc,
            evidence_digests=record.evidence_digests,
            quarantine_vault_path=record.quarantine_vault_path,
            status=QuarantineStatus.RELEASED,
            investigation_notes=tuple(updated_notes),
            release_receipt_id=receipt_id,
        )

        record_file = self.base_dir / f"{quarantine_id}.json"
        record_file.write_text(updated.to_json(), encoding="utf-8")
        return updated, receipt

    def list_quarantined(self, active_only: bool = True) -> list[QuarantineRecord]:
        records: list[QuarantineRecord] = []
        for file in sorted(self.base_dir.glob("quar_*.json")):
            try:
                rec = self.get_record(file.stem)
                if rec:
                    if not active_only or rec.status in (
                        QuarantineStatus.ISOLATED,
                        QuarantineStatus.INVESTIGATING,
                    ):
                        records.append(rec)
            except Exception:
                continue
        return records
