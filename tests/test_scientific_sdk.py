"""
Tests for CKODEX Scientific Kernel SDK:
- @scientific_node decorator (preflight hashing, execution, receipt minting, memory limit)
- ScientificDataConnector (FASTA parsing, PDB parsing, Lance conversion)
- AssetTombstoningEngine (cryptographic decommissioning, receipt verification)
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from ckodex_aiops.scientific.connectors import ScientificDataConnector
from ckodex_aiops.scientific.decorators import scientific_node
from ckodex_aiops.scientific.tombstone import AssetTombstoningEngine


def test_scientific_node_decorator_execution(tmp_path: Path):
    receipts_dir = tmp_path / "receipts"

    @scientific_node(
        domain="genomics",
        receipts_dir=receipts_dir,
    )
    def calculate_gc(sequence: str) -> float:
        seq = sequence.upper()
        return (seq.count("G") + seq.count("C")) / len(seq)

    result = calculate_gc("ATGCATGC")
    assert result == 0.5

    # Verify LineageReceipt was minted
    receipt_files = list(receipts_dir.glob("*.json"))
    assert len(receipt_files) == 1
    receipt_data = json.loads(receipt_files[0].read_text())
    assert receipt_data["node_name"] == "calculate_gc"
    assert receipt_data["attributes"]["domain"] == "genomics"
    assert len(receipt_data["input_digests"]) == 1
    assert len(receipt_data["output_digests"]) == 1


def test_scientific_node_memory_budget_enforcement(tmp_path: Path):
    receipts_dir = tmp_path / "receipts"

    # Extreme memory limit to trigger violation
    @scientific_node(
        domain="benchmarking",
        receipts_dir=receipts_dir,
        memory_limit_mb=0.0001,  # Unrealistically small: guaranteed to trigger
    )
    def allocate_memory():
        return [0] * 1000

    with pytest.raises(MemoryError, match="Rule #31 Bounded Resilience violation"):
        allocate_memory()


def test_scientific_node_to_kedro_node():
    @scientific_node(domain="structural_biology")
    def dummy_func(x: int) -> int:
        return x * 2

    kedro_node = dummy_func.to_kedro_node(inputs="input_val", outputs="output_val")
    assert kedro_node.name == "dummy_func"
    assert kedro_node.inputs == ["input_val"]
    assert kedro_node.outputs == ["output_val"]


def test_fasta_parsing_and_lance_ingestion(tmp_path: Path):
    connector = ScientificDataConnector(lance_store_dir=tmp_path / "lance")

    sample_fasta = (
        ">seq1 Human TP53 partial\n"
        "ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAG\n"
        ">seq2 Synthetic primer\n"
        "GCGCGCGCATATAT\n"
    )

    df = connector.parse_fasta(sample_fasta)
    assert df.height == 2
    assert "seq_id" in df.columns
    assert "gc_content" in df.columns
    assert df.filter(pl.col("seq_id") == "seq1")["length"][0] == 33

    # Ingest into Lance
    manifest = connector.ingest_to_lance("test_sequences", df)
    assert manifest.record_count == 2
    assert manifest.content_digest.startswith("sha256:")
    assert Path(manifest.destination_uri).exists()


def test_pdb_atom_parsing(tmp_path: Path):
    connector = ScientificDataConnector(lance_store_dir=tmp_path / "lance")

    sample_pdb = (
        "HEADER    PHOTOSYNTHETIC REACTION CENTER          28-OCT-99   1PRC              \n"
        "ATOM      1  N   PRO L   1      23.155  41.564  10.354  1.00 48.72           N  \n"
        "ATOM      2  CA  PRO L   1      24.411  42.138   9.827  1.00 48.72           C  \n"
        "HETATM 1001  O   HOH L 201      30.120  45.100  12.300  1.00 20.00           O  \n"
        "END                                                                             \n"
    )

    df = connector.parse_pdb_atoms(sample_pdb)
    assert df.height == 3
    assert "x" in df.columns
    assert "b_factor" in df.columns
    assert df.filter(pl.col("atom_serial") == 1)["res_name"][0] == "PRO"


def test_asset_tombstoning_decommission(tmp_path: Path):
    receipts_dir = tmp_path / "receipts"
    certs_dir = tmp_path / "tombstones"
    archive_dir = tmp_path / "archive"

    engine = AssetTombstoningEngine(
        receipts_dir=receipts_dir,
        certificates_dir=certs_dir,
    )

    test_model = tmp_path / "obsolete_weights.safetensors"
    test_model.write_bytes(b"MODEL_WEIGHT_BYTES_123456789")

    cert = engine.decommission(
        asset_path=test_model,
        reason="Model superseded by v0.4.0 (statistical sensor drift detected)",
        actor="lead:researcher",
        archive_target_dir=archive_dir,
        zeroize_local_file=True,
    )

    assert cert.asset_id == "obsolete_weights.safetensors"
    assert cert.state_vector["anti"] == "CONTRADICTS"
    assert not test_model.exists()  # Local file zeroized/unlinked
    assert cert.archived_uri is not None
    assert Path(cert.archived_uri).exists()  # Archived copy preserved

    # Verify tombstone certificate file exists
    cert_files = list(certs_dir.glob("*.json"))
    assert len(cert_files) == 1

    # Verify lineage receipt exists
    receipt_files = list(receipts_dir.glob("*.json"))
    assert len(receipt_files) == 1
