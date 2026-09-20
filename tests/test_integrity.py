"""
Tests for Data Integrity, Content-Addressable Digestion & Merkle Lineage Chains.
"""

from __future__ import annotations

import polars as pl
import pyarrow as pa
import torch

from ckodex_aiops.kernel.integrity import (
    ContentAddressableDigest,
    DataIntegrityEnvelope,
    MerkleLineageChain,
)
from ckodex_aiops.kernel.receipt import LineageReceipt


def test_polars_content_addressable_digestion():
    df1 = pl.DataFrame({"a": [1.0, 2.0, 3.0], "b": ["x", "y", "z"]})
    df2 = pl.DataFrame({"a": [1.0, 2.0, 3.0], "b": ["x", "y", "z"]})
    df_altered = pl.DataFrame({"a": [1.0, 2.0, 3.00001], "b": ["x", "y", "z"]})

    digest1 = ContentAddressableDigest.digest_polars(df1)
    digest2 = ContentAddressableDigest.digest_polars(df2)
    digest_alt = ContentAddressableDigest.digest_polars(df_altered)

    assert digest1.digest == digest2.digest
    assert digest1.digest != digest_alt.digest
    assert digest1.byte_count > 0


def test_arrow_content_addressable_digestion():
    t1 = pa.table({"val": [10, 20, 30], "label": ["cat", "dog", "bird"]})
    t2 = pa.table({"val": [10, 20, 30], "label": ["cat", "dog", "bird"]})
    t_altered = pa.table({"val": [10, 21, 30], "label": ["cat", "dog", "bird"]})

    d1 = ContentAddressableDigest.digest_arrow(t1)
    d2 = ContentAddressableDigest.digest_arrow(t2)
    d_alt = ContentAddressableDigest.digest_arrow(t_altered)

    assert d1.digest == d2.digest
    assert d1.digest != d_alt.digest


def test_torch_content_addressable_digestion():
    t1 = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)
    t2 = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)
    t_mod = torch.tensor([1.0, 2.0, 3.0001], dtype=torch.float32)

    d1 = ContentAddressableDigest.digest_torch(t1)
    d2 = ContentAddressableDigest.digest_torch(t2)
    d_mod = ContentAddressableDigest.digest_torch(t_mod)

    assert d1.digest == d2.digest
    assert d1.digest != d_mod.digest

    # Test state_dict
    sd1 = {"layer1.weight": torch.randn(4, 4), "layer1.bias": torch.zeros(4)}
    sd2 = {k: v.clone() for k, v in sd1.items()}
    sd_mod = {k: v.clone() for k, v in sd1.items()}
    sd_mod["layer1.bias"][0] += 0.01

    ds1 = ContentAddressableDigest.digest(sd1)
    ds2 = ContentAddressableDigest.digest(sd2)
    ds_mod = ContentAddressableDigest.digest(sd_mod)

    assert ds1.digest == ds2.digest
    assert ds1.digest != ds_mod.digest


def test_data_integrity_envelope():
    df = pl.DataFrame({"metric": [10.5, 20.2, 30.1]})
    digest = ContentAddressableDigest.digest(df)

    envelope = DataIntegrityEnvelope(
        artifact_id="art-telemetry-01",
        digest=digest,
        schema_signature="metric:Float64",
        row_or_param_count=3,
    )

    # Valid check
    assert envelope.verify(df) is True

    # Tampered check
    tampered_df = pl.DataFrame({"metric": [10.5, 20.2, 99.9]})
    assert envelope.verify(tampered_df) is False


def test_merkle_lineage_chain():
    # 1. Build sequence of receipts
    r0 = LineageReceipt(
        receipt_id="r0",
        intent_id="i0",
        node_name="node_ingest",
        authority_urn="urn:ckodex:test",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=10.0,
        timestamp_utc="2026-09-20T12:00:00Z",
        attributes={"parent_receipt_digest": ""},
    )
    d0 = r0.canonical_digest()

    r1 = LineageReceipt(
        receipt_id="r1",
        intent_id="i1",
        node_name="node_features",
        authority_urn="urn:ckodex:test",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=15.0,
        timestamp_utc="2026-09-20T12:01:00Z",
        attributes={"parent_receipt_digest": d0},
    )
    d1 = r1.canonical_digest()

    r2 = LineageReceipt(
        receipt_id="r2",
        intent_id="i2",
        node_name="node_train",
        authority_urn="urn:ckodex:test",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=25.0,
        timestamp_utc="2026-09-20T12:02:00Z",
        attributes={"parent_receipt_digest": d1},
    )

    # Validate valid chain
    is_valid, violations = MerkleLineageChain.validate_chain([r0, r1, r2])
    assert is_valid is True
    assert len(violations) == 0

    # Merkle root calculation
    root = MerkleLineageChain.build_merkle_root([d0, d1, r2.canonical_digest()])
    assert len(root) == 64

    # Test broken Merkle parent link
    r2_tampered = LineageReceipt(
        receipt_id="r2",
        intent_id="i2",
        node_name="node_train",
        authority_urn="urn:ckodex:test",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=25.0,
        timestamp_utc="2026-09-20T12:02:00Z",
        attributes={"parent_receipt_digest": "corrupted_parent_digest"},
    )
    is_valid_broken, violations_broken = MerkleLineageChain.validate_chain([r0, r1, r2_tampered])
    assert is_valid_broken is False
    assert any("broken Merkle link" in v for v in violations_broken)
