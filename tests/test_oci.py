"""Tests for OCI Artifact Packaging & Distribution Engine (OCI Spec v1.1.0)."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from ckodex_aiops.adapters.distribution.oci import (
    ARTIFACT_TYPE_CKODEX_TEMPLATE,
    MEDIA_TYPE_OCI_INDEX,
    OciTemplatePackager,
)


@pytest.fixture
def mock_repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "mock-repo"
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname = 'mock-aiops'\n", encoding="utf-8")
    (root / "justfile").write_text("default:\n    @just --list\n", encoding="utf-8")

    src = root / "src" / "mock_pkg"
    src.mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")

    # Excluded files
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (root / ".venv").mkdir()
    (root / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")

    # Mock compliance reporting files
    reporting = root / "data" / "08_reporting"
    (reporting / "sbom").mkdir(parents=True, exist_ok=True)
    (reporting / "sbom" / "cyclonedx.json").write_text(
        '{"bomFormat": "CycloneDX"}', encoding="utf-8"
    )
    (reporting / "sbom" / "spdx.json").write_text('{"spdxVersion": "SPDX-2.3"}', encoding="utf-8")
    (reporting / "oscal").mkdir(parents=True, exist_ok=True)
    (reporting / "oscal" / "component_definition.json").write_text(
        '{"oscal-version": "1.2"}', encoding="utf-8"
    )
    (reporting / "compliance").mkdir(parents=True, exist_ok=True)
    (reporting / "compliance" / "cortaix_csr_traceability_matrix.json").write_text(
        '{"framework": "cortAIx-Factory-CSR"}', encoding="utf-8"
    )

    return root


def test_create_template_archive(mock_repo_root: Path, tmp_path: Path):
    """Must build a clean tarball excluding .git, .venv, etc."""
    out_tar = tmp_path / "template.tar.gz"
    res = OciTemplatePackager.create_template_archive(mock_repo_root, out_tar)

    assert Path(res["path"]).exists()
    assert res["size_bytes"] > 0
    assert len(res["sha256"]) == 64
    assert res["file_count"] >= 4

    # Verify exclusions inside tarball
    with tarfile.open(out_tar, "r:gz") as tar:
        names = tar.getnames()
        assert "pyproject.toml" in names
        assert "justfile" in names
        assert "src/mock_pkg/__init__.py" in names
        assert not any(n.startswith(".git") for n in names)
        assert not any(n.startswith(".venv") for n in names)


def test_pack_and_inspect_oci_layout(mock_repo_root: Path, tmp_path: Path):
    """Must build fully compliant OCI Image Layout with index, manifest, config, and layers."""
    layout_dir = tmp_path / "oci-layout"
    _ = OciTemplatePackager.pack_oci_layout(
        source_root=mock_repo_root,
        output_layout_dir=layout_dir,
        template_version="2.0.0",
        tag="v2.0.0",
    )

    # 1. Check layout structure
    assert (layout_dir / "oci-layout").exists()
    assert (layout_dir / "index.json").exists()
    assert (layout_dir / "blobs" / "sha256").exists()

    # 2. Check index.json
    index_data = json.loads((layout_dir / "index.json").read_text(encoding="utf-8"))
    assert index_data["schemaVersion"] == 2
    assert index_data["mediaType"] == MEDIA_TYPE_OCI_INDEX
    assert len(index_data["manifests"]) == 1
    assert (
        index_data["manifests"][0]["annotations"]["org.opencontainers.image.ref.name"] == "v2.0.0"
    )

    # 3. Check inspection
    inspection = OciTemplatePackager.inspect_layout(layout_dir)
    assert inspection["artifact_type"] == ARTIFACT_TYPE_CKODEX_TEMPLATE
    assert inspection["config"]["version"] == "2.0.0"
    assert inspection["config"]["constitutionalStandard"] == "GAL 1"
    assert len(inspection["layers"]) >= 5  # Template + 2 SBOMs + OSCAL + CSR


def test_unpack_template_roundtrip(mock_repo_root: Path, tmp_path: Path):
    """Must unpack template archive from OCI layout and recreate source files faithfully."""
    layout_dir = tmp_path / "oci-layout"
    OciTemplatePackager.pack_oci_layout(source_root=mock_repo_root, output_layout_dir=layout_dir)

    dest_dir = tmp_path / "unpacked-project"
    res = OciTemplatePackager.unpack_template(layout_dir=layout_dir, destination_dir=dest_dir)

    assert Path(res["destination_dir"]).exists()
    assert (dest_dir / "pyproject.toml").exists()
    assert (dest_dir / "justfile").exists()
    assert (dest_dir / "src" / "mock_pkg" / "__init__.py").exists()
    assert res["files_unpacked"] >= 4


def test_generate_oras_commands():
    """Must generate standard ORAS and Cosign CLI instructions."""
    cmds = OciTemplatePackager.generate_oras_commands(
        image_ref="ghcr.io/org/repo:1.0.0", layout_dir="dist/oci-template"
    )
    assert "oras copy" in cmds["push_layout_with_oras"]
    assert "oras pull" in cmds["pull_with_oras"]
    assert "cosign sign" in cmds["cosign_sign"]
    assert "cosign attest" in cmds["cosign_attest_slsa"]
