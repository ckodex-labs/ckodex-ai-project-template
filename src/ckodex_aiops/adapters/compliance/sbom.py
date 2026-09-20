"""
Software Bill of Materials (SBOM) Generation Engine (CKODEX Rule #39).
Generates content-addressed CycloneDX v1.5 and SPDX 2.3 JSON representations
from locked UV dependency manifests and installed packages.
"""

from __future__ import annotations

import json
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.receipt import hash_file


class SbomGenerator:
    """
    Generates industry-standard CycloneDX and SPDX Software Bill of Materials (SBOM).
    """

    @classmethod
    def parse_uv_lock(cls, lockfile_path: str | Path = "uv.lock") -> list[dict[str, Any]]:
        """Parses packages from uv.lock."""
        p = Path(lockfile_path)
        if not p.exists():
            return []

        data = tomllib.loads(p.read_text(encoding="utf-8"))
        packages = []
        for pkg in data.get("package", []):
            name = pkg.get("name")
            version = pkg.get("version")
            if name and version:
                packages.append(
                    {
                        "name": name,
                        "version": version,
                        "purl": f"pkg:pypi/{name}@{version}",
                        "dependencies": [
                            d.get("name") for d in pkg.get("dependencies", []) if "name" in d
                        ],
                    }
                )
        return packages

    @classmethod
    def generate_cyclonedx(
        cls,
        packages: list[dict[str, Any]],
        project_name: str = "ckodex-aiops",
        project_version: str = "0.1.0",
        output_path: str | Path = "data/08_reporting/sbom/cyclonedx.json",
    ) -> dict[str, Any]:
        """Generates a CycloneDX v1.5 JSON SBOM."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        components = []
        for pkg in packages:
            components.append(
                {
                    "type": "library",
                    "bom-ref": pkg["purl"],
                    "name": pkg["name"],
                    "version": pkg["version"],
                    "purl": pkg["purl"],
                    "scope": "required",
                }
            )

        bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(UTC).isoformat(),
                "component": {
                    "type": "application",
                    "bom-ref": f"pkg:generic/{project_name}@{project_version}",
                    "name": project_name,
                    "version": project_version,
                    "description": "CKODEX AIOps Platform",
                },
                "manufacture": {
                    "name": "CKODEX Systems Architecture",
                },
            },
            "components": components,
        }

        out.write_text(json.dumps(bom, indent=2), encoding="utf-8")
        return {
            "path": str(out),
            "sha256": hash_file(out),
            "components_count": len(components),
            "spec": "CycloneDX 1.5",
        }

    @classmethod
    def generate_spdx(
        cls,
        packages: list[dict[str, Any]],
        project_name: str = "ckodex-aiops",
        project_version: str = "0.1.0",
        output_path: str | Path = "data/08_reporting/sbom/spdx.json",
    ) -> dict[str, Any]:
        """Generates an SPDX 2.3 JSON SBOM."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        doc_spdx_id = f"SPDXRef-Package-{project_name}"
        spdx_packages = [
            {
                "SPDXID": doc_spdx_id,
                "name": project_name,
                "versionInfo": project_version,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "Apache-2.0",
                "licenseDeclared": "Apache-2.0",
            }
        ]

        relationships = []
        for i, pkg in enumerate(packages):
            pkg_spdx_id = f"SPDXRef-Package-{pkg['name'].replace('_', '-')}-{i}"
            spdx_packages.append(
                {
                    "SPDXID": pkg_spdx_id,
                    "name": pkg["name"],
                    "versionInfo": pkg["version"],
                    "downloadLocation": "NOASSERTION",
                    "filesAnalyzed": False,
                    "externalRefs": [
                        {
                            "referenceCategory": "PACKAGE-MANAGER",
                            "referenceType": "purl",
                            "referenceLocator": pkg["purl"],
                        }
                    ],
                }
            )
            relationships.append(
                {
                    "spdxElementId": doc_spdx_id,
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": pkg_spdx_id,
                }
            )

        spdx_doc = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": f"{project_name}-sbom",
            "documentNamespace": f"https://ckodex.ai/spdx/{project_name}/{project_version}/{uuid.uuid4()}",
            "creationInfo": {
                "created": datetime.now(UTC).isoformat(),
                "creators": [
                    "Organization: CKODEX Systems Architecture",
                    "Tool: ckodex-aiops-sbom-1.0",
                ],
            },
            "packages": spdx_packages,
            "relationships": relationships,
        }

        out.write_text(json.dumps(spdx_doc, indent=2), encoding="utf-8")
        return {
            "path": str(out),
            "sha256": hash_file(out),
            "packages_count": len(spdx_packages),
            "spec": "SPDX 2.3",
        }
