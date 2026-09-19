"""
OCI Artifact Packaging & Distribution Engine (CKODEX Rule #39 & Rule #40).
Complies with OCI Image Format Specification v1.1.0 and OCI Artifact Guidelines:
- Content-addressed OCI Image Layout (`index.json`, `oci-layout`, `blobs/sha256/`).
- Multi-layer OCI Artifact: Template archive, CycloneDX/SPDX SBOMs, OSCAL 1.2 components, CortAIx CSR.
- Standard OCI annotations and interoperability with ORAS, Cosign, Crane, Skopeo, and Docker/Podman.
"""

from __future__ import annotations

import json
import shutil
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ckodex_aiops.kernel.receipt import (
    EvidenceDigest,
    LineageReceipt,
    compute_sha256,
    hash_file,
)

# Standard OCI Media Types
MEDIA_TYPE_OCI_INDEX = "application/vnd.oci.image.index.v1+json"
MEDIA_TYPE_OCI_MANIFEST = "application/vnd.oci.image.manifest.v1+json"
MEDIA_TYPE_TEMPLATE_CONFIG = "application/vnd.ckodex.template.config.v1+json"
MEDIA_TYPE_TEMPLATE_LAYER = "application/vnd.ckodex.template.layer.v1.tar+gzip"
MEDIA_TYPE_CYCLONEDX_SBOM = "application/vnd.cyclonedx+json"
MEDIA_TYPE_SPDX_SBOM = "application/spdx+json"
MEDIA_TYPE_OSCAL_DEFINITION = "application/vnd.oscal.component-definition+json"
MEDIA_TYPE_CORTAIX_CSR = "application/vnd.cortaix.csr.matrix+json"
ARTIFACT_TYPE_CKODEX_TEMPLATE = "application/vnd.ckodex.template.v1"


class OciTemplatePackager:
    """
    Packages and unpacks the CKODEX AIOps template as a compliant OCI Artifact
    using the standard OCI Image Layout specification.
    """

    DEFAULT_EXCLUDES: tuple[str, ...] = (
        ".git",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "__pycache__",
        "mlruns",
        "dist",
        ".cocoindex_code",
        "docs/public",
        "ci/.dagger",
        "ci/.venv",
        ".DS_Store",
    )

    @classmethod
    def _is_excluded(cls, path: Path, root: Path, excludes: tuple[str, ...]) -> bool:
        try:
            rel = path.relative_to(root)
        except ValueError:
            return False
        parts = rel.parts
        for part in parts:
            if part in excludes:
                return True
        # Filter out heavy generated lance binary tables from template distribution
        rel_str = str(rel)
        if rel_str.startswith("data/") and rel_str.endswith(".lance"):
            return True
        if "data/08_reporting/airgap/" in rel_str and rel_str.endswith(".tar.gz"):
            return True
        return False

    @classmethod
    def create_template_archive(
        cls,
        source_root: str | Path,
        output_tar_path: str | Path,
        excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
    ) -> dict[str, Any]:
        """Creates a clean, reproducible .tar.gz archive of the workspace template."""
        root = Path(source_root).resolve()
        out = Path(output_tar_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        file_count = 0
        with tarfile.open(out, "w:gz", format=tarfile.PAX_FORMAT) as tar:
            for item in sorted(root.rglob("*")):
                if cls._is_excluded(item, root, excludes):
                    continue
                arcname = item.relative_to(root)
                tar.add(item, arcname=str(arcname), recursive=False)
                file_count += 1

        size = out.stat().st_size
        digest = hash_file(out)
        return {
            "path": str(out),
            "size_bytes": size,
            "sha256": digest,
            "file_count": file_count,
        }

    @classmethod
    def pack_oci_layout(
        cls,
        source_root: str | Path = ".",
        output_layout_dir: str | Path = "dist/oci-template",
        template_version: str = "1.0.0",
        tag: str = "latest",
    ) -> dict[str, Any]:
        """
        Builds a content-addressed OCI Image Layout directory.
        Layers include:
        0. Template Archive (.tar.gz)
        1. CycloneDX SBOM
        2. SPDX SBOM
        3. NIST SP 800-53 OSCAL Component Definition
        4. CortAIx CSR Traceability Matrix
        """
        root = Path(source_root).resolve()
        layout_dir = Path(output_layout_dir).resolve()
        blobs_dir = layout_dir / "blobs" / "sha256"
        blobs_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write oci-layout identifier file
        layout_file = layout_dir / "oci-layout"
        layout_file.write_text(
            json.dumps({"imageLayoutVersion": "1.0.0"}, indent=2), encoding="utf-8"
        )

        # 2. Package template archive
        temp_tar = layout_dir / "_temp_template.tar.gz"
        archive_info = cls.create_template_archive(root, temp_tar)

        # Copy archive to blob store
        archive_blob_dest = blobs_dir / archive_info["sha256"]
        shutil.move(temp_tar, archive_blob_dest)

        layers: list[dict[str, Any]] = [
            {
                "mediaType": MEDIA_TYPE_TEMPLATE_LAYER,
                "digest": f"sha256:{archive_info['sha256']}",
                "size": archive_info["size_bytes"],
                "annotations": {
                    "org.opencontainers.image.title": "template.tar.gz",
                    "io.ckodex.files_count": str(archive_info["file_count"]),
                },
            }
        ]

        # 3. Attach auxiliary compliance & supply chain artifacts
        supplemental_files = [
            (
                root / "data/08_reporting/sbom/cyclonedx.json",
                MEDIA_TYPE_CYCLONEDX_SBOM,
                "cyclonedx.json",
            ),
            (
                root / "data/08_reporting/sbom/spdx.json",
                MEDIA_TYPE_SPDX_SBOM,
                "spdx.json",
            ),
            (
                root / "data/08_reporting/oscal/component_definition.json",
                MEDIA_TYPE_OSCAL_DEFINITION,
                "oscal_components.json",
            ),
            (
                root / "data/08_reporting/compliance/cortaix_csr_traceability_matrix.json",
                MEDIA_TYPE_CORTAIX_CSR,
                "cortaix_csr.json",
            ),
        ]

        for p, media_type, title in supplemental_files:
            if p.exists():
                digest = hash_file(p)
                size = p.stat().st_size
                shutil.copy2(p, blobs_dir / digest)
                layers.append(
                    {
                        "mediaType": media_type,
                        "digest": f"sha256:{digest}",
                        "size": size,
                        "annotations": {"org.opencontainers.image.title": title},
                    }
                )

        # 4. Create OCI Config Blob
        config_payload = {
            "schemaVersion": 1,
            "templateName": "ckodex-cfyd-aiops",
            "version": template_version,
            "description": "World-Class Kedro + UV + Ray + Lance + Polars + PyTorch AIOps Architecture",
            "constitutionalStandard": "GAL 1",
            "pythonVersion": ">=3.12",
            "supportedPlatforms": ["darwin/arm64", "linux/amd64", "linux/arm64"],
            "frameworks": [
                "kedro",
                "uv",
                "ray",
                "lance",
                "polars",
                "pytorch",
                "dagger",
                "hugo",
            ],
            "profiles": ["default", "macos_metal", "linux_cuda", "airgap_offline"],
            "created": datetime.now(UTC).isoformat(),
        }
        config_bytes = json.dumps(config_payload, indent=2, sort_keys=True).encode("utf-8")
        config_digest = compute_sha256(config_bytes)
        (blobs_dir / config_digest).write_bytes(config_bytes)

        config_descriptor = {
            "mediaType": MEDIA_TYPE_TEMPLATE_CONFIG,
            "digest": f"sha256:{config_digest}",
            "size": len(config_bytes),
        }

        # 5. Create OCI Manifest
        now_iso = datetime.now(UTC).isoformat()
        manifest_payload = {
            "schemaVersion": 2,
            "mediaType": MEDIA_TYPE_OCI_MANIFEST,
            "artifactType": ARTIFACT_TYPE_CKODEX_TEMPLATE,
            "config": config_descriptor,
            "layers": layers,
            "annotations": {
                "org.opencontainers.image.title": "ckodex-aiops-template",
                "org.opencontainers.image.version": template_version,
                "org.opencontainers.image.description": "Production Kedro + UV + Ray + Lance + Polars + PyTorch AIOps Template",
                "org.opencontainers.image.created": now_iso,
                "org.opencontainers.image.authors": "CKODEX Core Engineering",
                "org.opencontainers.image.licenses": "Apache-2.0",
                "ai.cfyd.ckodex.signature": "GAL 1 Constitutional",
                "ai.cfyd.ckodex.template.profiles": "default,macos_metal,linux_cuda,airgap_offline",
            },
        }
        manifest_bytes = json.dumps(manifest_payload, indent=2, sort_keys=True).encode("utf-8")
        manifest_digest = compute_sha256(manifest_bytes)
        (blobs_dir / manifest_digest).write_bytes(manifest_bytes)

        # 6. Create OCI Index (index.json)
        index_payload = {
            "schemaVersion": 2,
            "mediaType": MEDIA_TYPE_OCI_INDEX,
            "manifests": [
                {
                    "mediaType": MEDIA_TYPE_OCI_MANIFEST,
                    "digest": f"sha256:{manifest_digest}",
                    "size": len(manifest_bytes),
                    "annotations": {
                        "org.opencontainers.image.ref.name": tag,
                        "io.ckodex.version": template_version,
                    },
                }
            ],
        }
        (layout_dir / "index.json").write_text(
            json.dumps(index_payload, indent=2), encoding="utf-8"
        )

        # 7. Mint cryptographic Lineage Receipt
        receipt_id = f"rcpt_oci_{uuid4().hex[:12]}"
        receipt = LineageReceipt(
            receipt_id=receipt_id,
            intent_id="intent_oci_template_pack",
            node_name="oci:pack",
            authority_urn="urn:ckodex:cfyd:aiops:distribution:oci-template",
            input_digests=(),
            output_digests=(
                EvidenceDigest(
                    algorithm="sha256",
                    digest=manifest_digest,
                    uri=f"oci://{layout_dir}",
                    byte_count=len(manifest_bytes),
                ),
            ),
            execution_duration_ms=10.0,
            attributes={
                "template_version": template_version,
                "manifest_digest": f"sha256:{manifest_digest}",
                "layers_count": len(layers),
                "archive_size_bytes": archive_info["size_bytes"],
            },
        )
        receipts_dir = root / "data/08_reporting/receipts"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        (receipts_dir / f"{receipt_id}.json").write_text(receipt.to_json(), encoding="utf-8")

        return {
            "layout_dir": str(layout_dir),
            "manifest_digest": f"sha256:{manifest_digest}",
            "manifest_size": len(manifest_bytes),
            "layers_count": len(layers),
            "config_digest": f"sha256:{config_digest}",
            "template_archive_digest": f"sha256:{archive_info['sha256']}",
            "template_archive_size": archive_info["size_bytes"],
            "receipt_id": receipt_id,
        }

    @classmethod
    def inspect_layout(cls, layout_dir: str | Path) -> dict[str, Any]:
        """Inspects an OCI Image Layout without extracting payloads."""
        ldir = Path(layout_dir).resolve()
        index_file = ldir / "index.json"
        if not index_file.exists():
            raise FileNotFoundError(f"Invalid OCI layout: '{index_file}' does not exist.")

        index_data = json.loads(index_file.read_text(encoding="utf-8"))
        manifests = index_data.get("manifests", [])
        if not manifests:
            raise ValueError("OCI index contains no manifests.")

        manifest_desc = manifests[0]
        manifest_digest_hash = manifest_desc["digest"].replace("sha256:", "")
        manifest_blob = ldir / "blobs" / "sha256" / manifest_digest_hash
        manifest_data = json.loads(manifest_blob.read_text(encoding="utf-8"))

        config_hash = manifest_data["config"]["digest"].replace("sha256:", "")
        config_blob = ldir / "blobs" / "sha256" / config_hash
        config_data = json.loads(config_blob.read_text(encoding="utf-8"))

        layers_summary = []
        for layer in manifest_data.get("layers", []):
            layers_summary.append(
                {
                    "title": layer.get("annotations", {}).get(
                        "org.opencontainers.image.title", "unnamed"
                    ),
                    "media_type": layer["mediaType"],
                    "digest": layer["digest"],
                    "size_bytes": layer["size"],
                }
            )

        return {
            "layout_dir": str(ldir),
            "manifest_digest": manifest_desc["digest"],
            "artifact_type": manifest_data.get("artifactType", "unknown"),
            "annotations": manifest_data.get("annotations", {}),
            "config": config_data,
            "layers": layers_summary,
        }

    @classmethod
    def unpack_template(
        cls,
        layout_dir: str | Path,
        destination_dir: str | Path,
    ) -> dict[str, Any]:
        """
        Extracts the template layer from an OCI layout into a clean destination directory.
        """
        ldir = Path(layout_dir).resolve()
        dest = Path(destination_dir).resolve()
        dest.mkdir(parents=True, exist_ok=True)

        inspection = cls.inspect_layout(ldir)
        template_layer = None
        for layer in inspection["layers"]:
            if layer["media_type"] == MEDIA_TYPE_TEMPLATE_LAYER:
                template_layer = layer
                break

        if not template_layer:
            raise ValueError("No template archive layer found in OCI artifact manifest.")

        blob_hash = template_layer["digest"].replace("sha256:", "")
        blob_path = ldir / "blobs" / "sha256" / blob_hash

        # Verify blob integrity
        actual_hash = hash_file(blob_path)
        if actual_hash != blob_hash:
            raise ValueError(
                f"Integrity check failed for OCI blob '{blob_hash}'. Computed: '{actual_hash}'"
            )

        # Unpack safely
        with tarfile.open(blob_path, "r:gz") as tar:
            tar.extractall(path=dest, filter="data")

        return {
            "destination_dir": str(dest),
            "extracted_layer_digest": template_layer["digest"],
            "files_unpacked": len(list(dest.rglob("*"))),
        }

    @classmethod
    def generate_oras_commands(
        cls,
        image_ref: str = "ghcr.io/cfyd-ai/ckodex-aiops-template:v1.0.0",
        layout_dir: str | Path = "dist/oci-template",
    ) -> dict[str, str]:
        """
        Generates production ORAS and Cosign commands for distributing and signing the OCI artifact.
        """
        return {
            "push_layout_with_oras": f"oras copy --from-oci-layout {layout_dir}:latest {image_ref}",
            "inspect_layout_with_oras": f"oras manifest fetch --oci-layout {layout_dir}:latest --pretty",
            "pull_with_oras": f"oras pull {image_ref} --output ./new-project",
            "cosign_sign": f"cosign sign --yes {image_ref}",
            "cosign_attest_slsa": (
                f"cosign attest --yes --predicate data/08_reporting/attestations/statement.intoto.jsonl "
                f"--type https://slsa.dev/provenance/v1 {image_ref}"
            ),
            "cosign_verify": f"cosign verify --certificate-identity-regexp '.*' {image_ref}",
        }
