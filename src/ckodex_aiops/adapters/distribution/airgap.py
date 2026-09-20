"""
Air-Gap Content-Addressed Distribution Packager (CKODEX Rule #40).
Creates and verifies hermetic, offline distribution bundles containing
models, datasets, receipts, SLSA provenance, and living documentation.
"""

from __future__ import annotations

import json
import tarfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.receipt import hash_file
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)


class AirgapPackager:
    """
    Hermetic packager and verifier for disconnected / air-gapped environments.
    """

    @classmethod
    def create_bundle(
        cls,
        bundle_name: str,
        files_to_include: Sequence[str | Path],
        output_path: str | Path,
    ) -> dict[str, Any]:
        """
        Creates a content-addressed, self-describing tarball with an embedded SHA-256 manifest.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        manifest_entries: list[dict[str, Any]] = []
        valid_files: list[Path] = []

        for p_str in files_to_include:
            p = Path(p_str)
            if p.is_file():
                digest = hash_file(p)
                manifest_entries.append(
                    {
                        "path": str(p),
                        "size_bytes": p.stat().st_size,
                        "sha256": digest,
                    }
                )
                valid_files.append(p)
            elif p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file():
                        digest = hash_file(sub)
                        manifest_entries.append(
                            {
                                "path": str(sub),
                                "size_bytes": sub.stat().st_size,
                                "sha256": digest,
                            }
                        )
                        valid_files.append(sub)

        bundle_metadata = {
            "bundle_name": bundle_name,
            "created_at": datetime.now(UTC).isoformat(),
            "files_count": len(manifest_entries),
            "manifest": manifest_entries,
        }

        # Write tarball
        with tarfile.open(out, "w:gz") as tar:
            # First add manifest
            manifest_json = json.dumps(bundle_metadata, indent=2).encode("utf-8")
            import io

            tar_info = tarfile.TarInfo(name="bundle_manifest.json")
            tar_info.size = len(manifest_json)
            tar_info.mtime = int(datetime.now(UTC).timestamp())
            tar.addfile(tar_info, io.BytesIO(manifest_json))

            # Add all files
            for f in valid_files:
                tar.add(f, arcname=f"payload/{f}")

        bundle_digest = hash_file(out)
        bundle_metadata["bundle_sha256"] = bundle_digest
        bundle_metadata["bundle_path"] = str(out)

        return bundle_metadata

    @classmethod
    def verify_bundle(cls, bundle_path: str | Path) -> dict[str, Any]:
        """
        Verifies all checksums in an air-gap distribution bundle without extracting to disk.
        """
        bp = Path(bundle_path)
        if not bp.exists():
            raise FileNotFoundError(f"Bundle file '{bundle_path}' does not exist.")

        import hashlib

        with tarfile.open(bp, "r:gz") as tar:
            # Read manifest
            manifest_file = tar.extractfile("bundle_manifest.json")
            if manifest_file is None:
                raise ValueError("Corrupt bundle: 'bundle_manifest.json' not found.")
            manifest_data = json.loads(manifest_file.read().decode("utf-8"))

            mismatch_files: list[str] = []
            verified_files: list[str] = []

            for entry in manifest_data["manifest"]:
                arcname = f"payload/{entry['path']}"
                try:
                    f = tar.extractfile(arcname)
                    if f is None:
                        mismatch_files.append(entry["path"])
                        continue

                    h = hashlib.sha256()
                    while chunk := f.read(65536):
                        h.update(chunk)
                    computed = h.hexdigest()

                    if computed == entry["sha256"]:
                        verified_files.append(entry["path"])
                    else:
                        mismatch_files.append(entry["path"])
                except KeyError:
                    mismatch_files.append(entry["path"])

        is_valid = len(mismatch_files) == 0 and len(verified_files) == len(
            manifest_data["manifest"]
        )

        if is_valid:
            state_vec = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.POSITIVE,
                anti=Anti.NONE,
                coherence=Coherence.COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.NORMAL,
                metadata={"bundle": bp.name, "verified_files": len(verified_files)},
            )
        else:
            state_vec = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEGATIVE,
                anti=Anti.INVALIDATES,
                coherence=Coherence.DECOHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.QUARANTINED,
                metadata={"bundle": bp.name, "corrupt_files": mismatch_files},
            )

        return {
            "valid": is_valid,
            "bundle_sha256": hash_file(bp),
            "verified_count": len(verified_files),
            "mismatch_count": len(mismatch_files),
            "mismatch_files": mismatch_files,
            "state_vector": state_vec,
        }
