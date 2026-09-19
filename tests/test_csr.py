"""Tests for CortAIx CSR (Cybersecurity Requirements) Traceability Matrix Engine."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ckodex_aiops.adapters.compliance.csr import (
    CortaixCsrMatrixGenerator,
)


def test_csr_canonical_controls_loading():
    """Must load 107 controls from CortAIx CSR catalog."""
    controls = CortaixCsrMatrixGenerator.load_canonical_controls()
    assert len(controls) == 107

    # Verify key control IDs
    cids = [c["control_id"] for c in controls]
    assert "FPR-TRAC" in cids
    assert "TRR-PLAN" in cids
    assert "TRR-DOCU" in cids
    assert "TRR-TRAC" in cids
    assert "PRR-PRD-SRAV" in cids
    assert "PRR-PRD-CHGP" in cids
    assert "PRR-PRD-ISOP" in cids
    assert "PRR-REL-MALW" in cids
    assert "PRR-REL-SIGN" in cids
    assert "PRR-REL-SBOM" in cids


def test_csr_build_traceability_matrix():
    """Must build matrix binding controls to technical implementations."""
    matrix = CortaixCsrMatrixGenerator.build_traceability_matrix()
    assert len(matrix) == 107

    lookup = {m["control_id"]: m for m in matrix}

    # Verify implementation details and evidence
    assert lookup["FPR-TRAC"]["status"] == "implemented"
    assert lookup["TRR-PLAN"]["status"] == "implemented"
    assert lookup["PRR-REL-SBOM"]["status"] == "implemented"
    assert (
        "uv.lock" in lookup["PRR-REL-SBOM"]["evidence_ref"]
        or "sbom" in lookup["PRR-REL-SBOM"]["evidence_ref"]
    )
    assert lookup["CFY-DSG-ZERO"]["status"] == "implemented"


def test_csr_export_all(tmp_path: Path):
    """Must export JSON, CSV, and Markdown traceability reports with cryptographic receipts."""
    out_dir = tmp_path / "compliance"
    res = CortaixCsrMatrixGenerator.export_all(output_dir=out_dir)

    assert Path(res["json"]).exists()
    assert Path(res["csv"]).exists()
    assert Path(res["markdown"]).exists()
    assert len(res["json_sha256"]) == 64

    # Verify JSON structure
    json_data = json.loads(Path(res["json"]).read_text(encoding="utf-8"))
    assert json_data["framework"] == "cortAIx-Factory-CSR"
    assert json_data["total_controls"] == 107
    assert json_data["implemented_count"] >= 35
    assert len(json_data["controls"]) == 107

    # Verify CSV structure
    with open(res["csv"], encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 107
        assert "control_id" in rows[0]
        assert "status" in rows[0]

    # Verify Markdown report
    md_content = Path(res["markdown"]).read_text(encoding="utf-8")
    assert "CortAIx Factory CSR — Security Traceability Matrix" in md_content
    assert "Release Gate Readiness" in md_content
    assert "PRR-REL-SBOM" in md_content
