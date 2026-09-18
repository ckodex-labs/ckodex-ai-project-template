"""
Pure Semantic Kernel: Lineage Receipts and Evidence Digests.
Complies with CKODEX Architectural Signature: Proof Before and Receipt After.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def compute_sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class EvidenceDigest:
    algorithm: str = "sha256"
    digest: str = ""
    uri: str = ""
    byte_count: int = 0


@dataclass(frozen=True)
class LineageReceipt:
    """
    Immutable execution receipt emitted after state transition or node completion.
    M = <S0, Trigger, Authority, Transformation, S1, Evidence, Time>
    """

    receipt_id: str
    intent_id: str
    node_name: str
    authority_urn: str
    input_digests: tuple[EvidenceDigest, ...]
    output_digests: tuple[EvidenceDigest, ...]
    execution_duration_ms: float
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def canonical_digest(self) -> str:
        payload = {
            "receipt_id": self.receipt_id,
            "intent_id": self.intent_id,
            "node_name": self.node_name,
            "authority_urn": self.authority_urn,
            "timestamp_utc": self.timestamp_utc,
            "duration_ms": self.execution_duration_ms,
        }
        return compute_sha256(json.dumps(payload, sort_keys=True))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
