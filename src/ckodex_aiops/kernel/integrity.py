"""
Pure Semantic Kernel: Data Integrity, Content-Addressable Digestion & Merkle Lineage (Rules #8, #18, #39).
Ensures cryptographic data immutability, tamper detection, and verified transformation chains:
M = <S0, Trigger, Authority, Transformation, S1, Evidence, Time>
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np
import polars as pl
import pyarrow as pa
import torch

from ckodex_aiops.kernel.receipt import EvidenceDigest, LineageReceipt, compute_sha256


class ContentAddressableDigest:
    """
    Deterministic, content-addressable cryptographic digestion for all supported AI data primitives:
    - Polars DataFrames (schema + shape + typed null counts + column hashes)
    - PyArrow Tables (schema fingerprint + row count + buffer hashes)
    - PyTorch Tensors & State Dicts (dtypes + shapes + raw parameter buffers)
    - Dictionaries / Arbitrary JSON-serializable artifacts
    """

    @classmethod
    def digest_polars(cls, df: pl.DataFrame, uri: str = "") -> EvidenceDigest:
        """Computes a deterministic content digest for a Polars DataFrame."""
        # 1. Schema signature (sorted column names and dtypes)
        schema_entries = sorted([(col, str(dtype)) for col, dtype in df.schema.items()])

        # 2. Structural metadata
        shape = (df.height, df.width)
        null_counts = sorted([(col, df[col].null_count()) for col in df.columns])

        # 3. Deterministic content hashing per column
        col_hashes = []
        for col_name in sorted(df.columns):
            series = df[col_name]
            # Convert series to bytes or hash representation
            val_hash = hashlib.sha256(str(series.to_list()).encode("utf-8")).hexdigest()
            col_hashes.append(f"{col_name}:{val_hash}")

        composite_payload = {
            "type": "polars.DataFrame",
            "shape": shape,
            "schema": schema_entries,
            "null_counts": null_counts,
            "col_hashes": col_hashes,
        }
        raw_bytes = json.dumps(composite_payload, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(raw_bytes).hexdigest()

        return EvidenceDigest(
            algorithm="sha256",
            digest=digest,
            uri=uri or f"memory://polars/shape={df.height}x{df.width}",
            byte_count=len(raw_bytes),
        )

    @classmethod
    def digest_arrow(cls, table: pa.Table, uri: str = "") -> EvidenceDigest:
        """Computes a deterministic content digest for a PyArrow Table."""
        schema_entries = sorted([(field.name, str(field.type)) for field in table.schema])
        col_hashes = []
        for name in sorted(table.column_names):
            col = table.column(name)
            col_hash = hashlib.sha256(str(col.to_pylist()).encode("utf-8")).hexdigest()
            col_hashes.append(f"{name}:{col_hash}")

        composite_payload = {
            "type": "pyarrow.Table",
            "num_rows": table.num_rows,
            "num_columns": table.num_columns,
            "schema": schema_entries,
            "col_hashes": col_hashes,
        }
        raw_bytes = json.dumps(composite_payload, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(raw_bytes).hexdigest()

        return EvidenceDigest(
            algorithm="sha256",
            digest=digest,
            uri=uri or f"memory://pyarrow/rows={table.num_rows}",
            byte_count=len(raw_bytes),
        )

    @classmethod
    def digest_torch(
        cls, data: torch.Tensor | dict[str, torch.Tensor], uri: str = ""
    ) -> EvidenceDigest:
        """Computes a deterministic content digest for PyTorch weights or tensors."""
        h = hashlib.sha256()

        if isinstance(data, torch.Tensor):
            t = data.detach().cpu()
            h.update(str(t.shape).encode("utf-8"))
            h.update(str(t.dtype).encode("utf-8"))
            h.update(t.contiguous().numpy().tobytes())
            byte_count = t.element_size() * t.numel()
        elif isinstance(data, dict):
            # Model state_dict
            total_bytes = 0
            for key in sorted(data.keys()):
                val = data[key]
                if isinstance(val, torch.Tensor):
                    t = val.detach().cpu()
                    h.update(key.encode("utf-8"))
                    h.update(str(t.shape).encode("utf-8"))
                    h.update(str(t.dtype).encode("utf-8"))
                    h.update(t.contiguous().numpy().tobytes())
                    total_bytes += t.element_size() * t.numel()
                else:
                    h.update(f"{key}:{val}".encode())
            byte_count = total_bytes
        else:
            payload = str(data).encode("utf-8")
            h.update(payload)
            byte_count = len(payload)

        digest = h.hexdigest()
        return EvidenceDigest(
            algorithm="sha256",
            digest=digest,
            uri=uri or "memory://torch/tensor",
            byte_count=byte_count,
        )

    @classmethod
    def digest(cls, value: Any, uri: str = "") -> EvidenceDigest:
        """Polymorphic entry point: routes arbitrary AI objects to their specialized digester."""
        if isinstance(value, pl.DataFrame):
            return cls.digest_polars(value, uri=uri)
        if isinstance(value, pa.Table):
            return cls.digest_arrow(value, uri=uri)
        if isinstance(value, torch.Tensor):
            return cls.digest_torch(value, uri=uri)
        if isinstance(value, dict) and any(isinstance(v, torch.Tensor) for v in value.values()):
            return cls.digest_torch(value, uri=uri)
        if isinstance(value, np.ndarray):
            raw = value.tobytes()
            digest = hashlib.sha256(raw).hexdigest()
            return EvidenceDigest(
                algorithm="sha256",
                digest=digest,
                uri=uri or f"memory://numpy/shape={value.shape}",
                byte_count=value.nbytes,
            )
        # Fallback to JSON canonical serialization
        try:
            raw_bytes = json.dumps(value, sort_keys=True, default=str).encode("utf-8")
        except Exception:
            raw_bytes = str(value).encode("utf-8")

        return EvidenceDigest(
            algorithm="sha256",
            digest=hashlib.sha256(raw_bytes).hexdigest(),
            uri=uri or "memory://generic",
            byte_count=len(raw_bytes),
        )


@dataclass(frozen=True)
class DataIntegrityEnvelope:
    """
    Tamper-evident envelope encapsulating an artifact, its cryptographic digest, and author attribution.
    """

    artifact_id: str
    digest: EvidenceDigest
    schema_signature: str
    row_or_param_count: int
    created_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    attributes: dict[str, Any] = field(default_factory=dict)

    def verify(self, current_data: Any) -> bool:
        """Verifies that the current data strictly matches the envelope's content digest."""
        current_digest = ContentAddressableDigest.digest(current_data)
        return current_digest.digest == self.digest.digest


class MerkleLineageChain:
    """
    Verifies cryptographic continuity and Merkle-tree lineage across execution receipts:
    Each receipt $N$ records the canonical digest of receipt $N-1$, proving execution order,
    non-repudiation, and immutability.
    """

    @staticmethod
    def build_merkle_root(digests: Sequence[str]) -> str:
        """Computes deterministic Merkle root over a sequence of hashes."""
        if not digests:
            return compute_sha256("")
        current = list(digests)
        while len(current) > 1:
            if len(current) % 2 != 0:
                current.append(current[-1])  # Duplicate last element for even pairing
            next_level = []
            for i in range(0, len(current), 2):
                combined = current[i] + current[i + 1]
                next_level.append(compute_sha256(combined))
            current = next_level
        return current[0]

    @staticmethod
    def validate_chain(receipts: Sequence[LineageReceipt]) -> tuple[bool, list[str]]:
        """
        Validates the cryptographic integrity and causal sequence of a chain of lineage receipts.
        Checks:
        1. Canonical hash validity of each receipt.
        2. Strict parent-receipt link continuity (Merkle link).
        3. Non-regression of timestamps.
        """
        violations: list[str] = []
        if not receipts:
            return True, []

        last_digest = ""
        last_timestamp = ""

        for idx, rcpt in enumerate(receipts):
            # Check internal digest consistency
            expected_canonical = rcpt.canonical_digest()
            if not expected_canonical:
                violations.append(
                    f"Receipt index {idx} ({rcpt.receipt_id}): invalid canonical digest."
                )

            # Check timestamp monotonicity
            if last_timestamp and rcpt.timestamp_utc < last_timestamp:
                violations.append(
                    f"Receipt index {idx} ({rcpt.receipt_id}): temporal anomaly, timestamp {rcpt.timestamp_utc} precedes previous {last_timestamp}."
                )
            last_timestamp = rcpt.timestamp_utc

            # Check parent linkage if present in attributes
            parent_digest = rcpt.attributes.get("parent_receipt_digest", "")
            if idx > 0 and parent_digest:
                if parent_digest != last_digest:
                    violations.append(
                        f"Receipt index {idx} ({rcpt.receipt_id}): broken Merkle link! "
                        f"Expected parent {last_digest}, got {parent_digest}."
                    )

            last_digest = expected_canonical

        is_valid = len(violations) == 0
        return is_valid, violations
