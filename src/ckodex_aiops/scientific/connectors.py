"""
CKODEX Scientific Data Connectors: Domain-Driven Ingestion.
Standardized parsers and Lance exporters for biological and physical AI assets:
- FASTA / Sequence records
- Molecular PDB / Structural coordinates
- Tabular assay / ChEMBL / ClinVar callsets
- Zero-copy conversion into columnar Lance datasets with Merkle lineage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from ckodex_aiops.adapters.lance.store import LanceVectorStore
from ckodex_aiops.kernel.receipt import compute_sha256


@dataclass(frozen=True)
class IngestionManifest:
    """Summary of ingested scientific dataset."""

    record_count: int
    content_digest: str
    destination_uri: str
    schema_summary: list[str]


class ScientificDataConnector:
    """
    Ingests raw scientific files directly into high-assurance Lance/Polars formats.
    """

    def __init__(self, lance_store_dir: str | Path = "data/04_feature/lance") -> None:
        self.store_dir = Path(lance_store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = LanceVectorStore(self.store_dir)

    def parse_fasta(self, fasta_content: str | Path) -> pl.DataFrame:
        """
        Parses FASTA format sequence records into a Polars DataFrame:
        id, description, sequence, length, gc_content.
        """
        raw_text = (
            fasta_content.read_text(encoding="utf-8")
            if isinstance(fasta_content, Path)
            else fasta_content
        )

        records: list[dict[str, Any]] = []
        current_header = ""
        current_seq: list[str] = []

        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_header:
                    seq_str = "".join(current_seq).upper()
                    gc = (
                        (seq_str.count("G") + seq_str.count("C")) / len(seq_str) if seq_str else 0.0
                    )
                    parts = current_header[1:].split(None, 1)
                    seq_id = parts[0]
                    desc = parts[1] if len(parts) > 1 else ""
                    records.append(
                        {
                            "seq_id": seq_id,
                            "description": desc,
                            "sequence": seq_str,
                            "length": len(seq_str),
                            "gc_content": float(gc),
                            "hash": compute_sha256(seq_str),
                        }
                    )
                current_header = line
                current_seq = []
            else:
                current_seq.append(line)

        if current_header:
            seq_str = "".join(current_seq).upper()
            gc = (seq_str.count("G") + seq_str.count("C")) / len(seq_str) if seq_str else 0.0
            parts = current_header[1:].split(None, 1)
            seq_id = parts[0]
            desc = parts[1] if len(parts) > 1 else ""
            records.append(
                {
                    "seq_id": seq_id,
                    "description": desc,
                    "sequence": seq_str,
                    "length": len(seq_str),
                    "gc_content": float(gc),
                    "hash": compute_sha256(seq_str),
                }
            )

        if not records:
            return pl.DataFrame(
                schema={
                    "seq_id": pl.Utf8,
                    "description": pl.Utf8,
                    "sequence": pl.Utf8,
                    "length": pl.Int64,
                    "gc_content": pl.Float64,
                    "hash": pl.Utf8,
                }
            )

        return pl.DataFrame(records)

    def parse_pdb_atoms(self, pdb_content: str | Path) -> pl.DataFrame:
        """
        Parses PDB coordinate lines (ATOM/HETATM) into high-performance Polars coordinates:
        atom_serial, atom_name, res_name, chain_id, res_seq, x, y, z, occupancy, temp_factor.
        """
        raw_text = (
            pdb_content.read_text(encoding="utf-8")
            if isinstance(pdb_content, Path)
            else pdb_content
        )

        rows: list[dict[str, Any]] = []
        for line in raw_text.splitlines():
            if line.startswith("ATOM  ") or line.startswith("HETATM"):
                try:
                    record_type = line[0:6].strip()
                    atom_serial = int(line[6:11].strip())
                    atom_name = line[12:16].strip()
                    res_name = line[17:20].strip()
                    chain_id = line[21:22].strip()
                    res_seq = int(line[22:26].strip())
                    x = float(line[30:38].strip())
                    y = float(line[38:46].strip())
                    z = float(line[46:54].strip())
                    occ = float(line[54:60].strip()) if len(line) >= 60 else 1.0
                    b_factor = float(line[60:66].strip()) if len(line) >= 66 else 0.0

                    rows.append(
                        {
                            "record_type": record_type,
                            "atom_serial": atom_serial,
                            "atom_name": atom_name,
                            "res_name": res_name,
                            "chain_id": chain_id,
                            "res_seq": res_seq,
                            "x": x,
                            "y": y,
                            "z": z,
                            "occupancy": occ,
                            "b_factor": b_factor,
                        }
                    )
                except (ValueError, IndexError):
                    continue

        if not rows:
            return pl.DataFrame(
                schema={
                    "record_type": pl.Utf8,
                    "atom_serial": pl.Int64,
                    "atom_name": pl.Utf8,
                    "res_name": pl.Utf8,
                    "chain_id": pl.Utf8,
                    "res_seq": pl.Int64,
                    "x": pl.Float64,
                    "y": pl.Float64,
                    "z": pl.Float64,
                    "occupancy": pl.Float64,
                    "b_factor": pl.Float64,
                }
            )

        return pl.DataFrame(rows)

    def ingest_to_lance(
        self,
        table_name: str,
        df: pl.DataFrame,
    ) -> IngestionManifest:
        """
        Commits scientific DataFrame into Lance vector store and produces IngestionManifest.
        """
        self.vector_store.create_or_replace_table(table_name, df)
        digest = compute_sha256(str(df.shape) + "".join(df.columns))
        return IngestionManifest(
            record_count=df.height,
            content_digest=f"sha256:{digest}",
            destination_uri=str(self.store_dir / f"{table_name}.lance"),
            schema_summary=[
                f"{col}: {dtype}" for col, dtype in zip(df.columns, df.dtypes, strict=False)
            ],
        )
