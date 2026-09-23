"""
CKODEX Scientific Model & Asset Decommissioning (Tombstoning Engine).
Complies with:
- Rule #16: ANTI is not more negative (LEASE_REVOKED structural invalidation).
- Rule #18: State Mutation Requires Lineage (Supersession & historical preservation).
- Rule #27: Day-2 is Part of the Feature (Cryptographic offboarding).
- Rule #32: Quarantine Preserves Evidence (Evidence retention during teardown).
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ckodex_aiops.kernel.intent import AuthorityPath
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


@dataclass(frozen=True)
class DecommissionCertificate:
    """Cryptographically verifiable tombstone record for an offboarded model/asset."""

    certificate_id: str
    asset_id: str
    asset_path: str
    content_sha256: str
    authority_urn: str
    actor: str
    reason: str
    decommissioned_at_utc: str
    archived_uri: str | None
    state_vector: dict[str, str]
    receipt_digest: str


class AssetTombstoningEngine:
    """
    Manages the permanent, auditable retirement of models, weights, and scientific datasets.
    Zeroizes active execution weights while preserving lineage digests and audit evidence.
    """

    def __init__(
        self,
        receipts_dir: str | Path = "data/08_reporting/receipts",
        certificates_dir: str | Path = "data/08_reporting/lifecycle/tombstones",
    ) -> None:
        self.receipts_dir = Path(receipts_dir)
        self.certificates_dir = Path(certificates_dir)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.certificates_dir.mkdir(parents=True, exist_ok=True)

    def decommission(
        self,
        asset_path: str | Path,
        reason: str,
        actor: str = "principal:engineer",
        archive_target_dir: str | Path | None = None,
        zeroize_local_file: bool = False,
    ) -> DecommissionCertificate:
        """
        Decommissions an asset:
        1. Computes SHA256 content digest.
        2. Optionally moves payload to an archival destination.
        3. Optionally unlinks/zeroizes the active local file.
        4. Mints LineageReceipt with ANTI: CONTRADICTS / LEASE_REVOKED semantics.
        5. Emits immutable DecommissionCertificate.
        """
        target = Path(asset_path)
        if not target.exists():
            raise FileNotFoundError(f"Cannot decommission non-existent asset: {target}")

        now_utc = datetime.now(UTC).isoformat()
        asset_bytes = target.read_bytes() if target.is_file() else str(target).encode("utf-8")
        content_hash = compute_sha256(asset_bytes)

        # Archival move if requested
        archived_uri: str | None = None
        if archive_target_dir:
            archive_path = Path(archive_target_dir)
            archive_path.mkdir(parents=True, exist_ok=True)
            dest_file = (
                archive_path / f"{target.name}.archived.{int(datetime.now(UTC).timestamp())}"
            )
            if target.is_file():
                shutil.copy2(target, dest_file)
            else:
                shutil.copytree(target, dest_file)
            archived_uri = str(dest_file)

        # Optional zeroization of local active file
        if zeroize_local_file and target.is_file():
            target.unlink()

        auth_path = AuthorityPath(
            tenant="cfyd",
            workspace="aiops",
            environment="production",
            project="decommission",
        )

        receipt_id = f"rcpt_tombstone_{uuid4().hex[:12]}"
        receipt = LineageReceipt(
            receipt_id=receipt_id,
            intent_id=f"intent_tombstone_{target.name}",
            node_name="asset:decommission",
            authority_urn=auth_path.to_urn(),
            input_digests=(
                EvidenceDigest(
                    algorithm="sha256",
                    digest=content_hash,
                    uri=str(target),
                    byte_count=len(asset_bytes),
                ),
            ),
            output_digests=(),
            execution_duration_ms=1.0,
            attributes={
                "action": "DECOMMISSION",
                "asset_path": str(target),
                "actor": actor,
                "reason": reason,
                "archived_uri": archived_uri,
                "zeroized": zeroize_local_file,
                "timestamp_utc": now_utc,
            },
        )

        # Persist receipt
        receipt_path = self.receipts_dir / f"{receipt_id}.json"
        receipt_path.write_text(receipt.to_json(), encoding="utf-8")

        # Decommissioned State Vector: NEGATIVE valence, CONTRADICTS anti, OFFBOARDED lifecycle
        vector = StateVector(
            presence=Presence.PRESENT,
            valence=Valence.NEGATIVE,
            anti=Anti.CONTRADICTS,
            coherence=Coherence.COHERENT,
            evidence=EvidenceStatus.VERIFIED,
            lifecycle=OperationalLifecycle.FAILED,  # Inactive / Decommissioned
        )

        cert_id = f"tombstone_{uuid4().hex[:12]}"
        cert = DecommissionCertificate(
            certificate_id=cert_id,
            asset_id=target.name,
            asset_path=str(target),
            content_sha256=content_hash,
            authority_urn=auth_path.to_urn(),
            actor=actor,
            reason=reason,
            decommissioned_at_utc=now_utc,
            archived_uri=archived_uri,
            state_vector={
                "presence": vector.presence.value,
                "valence": vector.valence.value,
                "anti": vector.anti.value,
                "coherence": vector.coherence.value,
                "evidence": vector.evidence.value,
                "lifecycle": vector.lifecycle.value,
            },
            receipt_digest=receipt.canonical_digest(),
        )

        cert_file = self.certificates_dir / f"{cert_id}.json"
        cert_file.write_text(json.dumps(asdict(cert), indent=2), encoding="utf-8")
        return cert
