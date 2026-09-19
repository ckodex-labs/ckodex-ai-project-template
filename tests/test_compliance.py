"""Tests for Compliance Adapters: In-toto SLSA Provenance and NIST SP 800-53 OSCAL."""

from __future__ import annotations

from ckodex_aiops.adapters.compliance.intoto import IntotoProvenanceAttestor
from ckodex_aiops.adapters.compliance.oscal import OscalComplianceGenerator


def test_intoto_slsa_provenance_generation(tmp_path):
    """Must generate standard In-toto v1.0 Statement with SLSA Provenance v1.0 predicate."""
    # Create dummy artifact
    test_artifact = tmp_path / "model.safetensors"
    test_artifact.write_bytes(b"mock_safetensors_bytes_12345")

    stmt = IntotoProvenanceAttestor.generate_attestation(
        subject_path=test_artifact,
        invocation_params={"epochs": 10, "profile": "macos_metal"},
    )

    assert stmt["_type"] == "https://in-toto.io/Statement/v1"
    assert stmt["predicateType"] == "https://slsa.dev/provenance/v1"
    assert len(stmt["subject"]) == 1
    assert "sha256" in stmt["subject"][0]["digest"]

    # Write to disk
    out_file = tmp_path / "statement.intoto.jsonl"
    saved = IntotoProvenanceAttestor.write_attestation(stmt, out_file)
    assert saved.exists()


def test_oscal_component_definition_generation(tmp_path):
    """Must generate machine-verifiable NIST SP 800-53 Rev 5 OSCAL schema."""
    doc = OscalComplianceGenerator.generate_component_definition()
    assert "component-definition" in doc
    comp = doc["component-definition"]
    assert "components" in comp
    assert len(comp["components"]) >= 1

    all_control_ids = [
        req["control-id"]
        for component in comp["components"]
        for impl in component.get("control-implementations", [])
        for req in impl.get("implemented-requirements", [])
    ]
    assert "ac-3" in all_control_ids
    assert "au-2" in all_control_ids
    assert "sc-13" in all_control_ids
    assert "si-7" in all_control_ids

    out_file = tmp_path / "oscal_component.json"
    saved = OscalComplianceGenerator.write_oscal(output_path=out_file)
    assert saved.exists()
