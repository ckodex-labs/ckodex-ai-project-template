"""Tests for SBOM Generator: CycloneDX v1.5 and SPDX 2.3 JSON compliance."""

from __future__ import annotations

import json
from pathlib import Path

from ckodex_aiops.adapters.compliance.sbom import SbomGenerator


def test_parse_uv_lock(tmp_path: Path):
    """Must accurately parse packages from uv.lock format."""
    mock_lock = tmp_path / "uv.lock"
    mock_lock.write_text(
        """
version = 1
revision = 1

[[package]]
name = "torch"
version = "2.4.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "typing-extensions" },
]

[[package]]
name = "typing-extensions"
version = "4.12.2"
source = { registry = "https://pypi.org/simple" }
""",
        encoding="utf-8",
    )

    packages = SbomGenerator.parse_uv_lock(mock_lock)
    assert len(packages) == 2
    names = [p["name"] for p in packages]
    assert "torch" in names
    assert "typing-extensions" in names
    assert packages[0]["purl"] == "pkg:pypi/torch@2.4.0"


def test_generate_cyclonedx(tmp_path: Path):
    """Must generate standard CycloneDX v1.5 JSON SBOM."""
    packages = [
        {"name": "polars", "version": "1.6.0", "purl": "pkg:pypi/polars@1.6.0", "dependencies": []},
        {"name": "lance", "version": "0.19.0", "purl": "pkg:pypi/lance@0.19.0", "dependencies": []},
    ]
    out_file = tmp_path / "sbom" / "cyclonedx.json"
    res = SbomGenerator.generate_cyclonedx(packages, output_path=out_file)

    assert Path(res["path"]).exists()
    assert res["components_count"] == 2
    assert len(res["sha256"]) == 64

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["bomFormat"] == "CycloneDX"
    assert data["specVersion"] == "1.5"
    assert len(data["components"]) == 2
    assert data["metadata"]["component"]["name"] == "ckodex-aiops"


def test_generate_spdx(tmp_path: Path):
    """Must generate standard SPDX 2.3 JSON document."""
    packages = [
        {"name": "polars", "version": "1.6.0", "purl": "pkg:pypi/polars@1.6.0", "dependencies": []},
    ]
    out_file = tmp_path / "sbom" / "spdx.json"
    res = SbomGenerator.generate_spdx(packages, output_path=out_file)

    assert Path(res["path"]).exists()
    assert res["packages_count"] == 2  # Root document package + polars
    assert len(res["sha256"]) == 64

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["spdxVersion"] == "SPDX-2.3"
    assert data["SPDXID"] == "SPDXRef-DOCUMENT"
    assert len(data["packages"]) == 2
    assert len(data["relationships"]) == 1
    assert data["relationships"][0]["relationshipType"] == "DEPENDS_ON"
