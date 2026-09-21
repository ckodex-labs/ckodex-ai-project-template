"""Tests for Air-Gap Content-Addressed Distribution Packager.
Validates bundle creation, manifest verification, and tamper detection.
"""

from __future__ import annotations

from ckodex_aiops.adapters.distribution.airgap import AirgapPackager
from ckodex_aiops.kernel.state_vector import OperationalLifecycle


def test_airgap_bundle_lifecycle(tmp_path):
    """Must package files with SHA-256 manifests and verify cleanly offline."""
    # Create test artifacts
    art_a = tmp_path / "model.safetensors"
    art_a.write_bytes(b"model_weights_tensor_content_123")
    art_b = tmp_path / "provenance.json"
    art_b.write_text('{"slsa": "v1.0"}')

    bundle_out = tmp_path / "airgap_bundle.tar.gz"

    # 1. Package
    meta = AirgapPackager.create_bundle(
        bundle_name="test-airgap-pkg",
        files_to_include=[art_a, art_b],
        output_path=bundle_out,
    )
    assert bundle_out.exists()
    assert meta["files_count"] == 2
    assert len(meta["bundle_sha256"]) == 64

    # 2. Verify
    ver = AirgapPackager.verify_bundle(bundle_out)
    assert ver["valid"] is True
    assert ver["verified_count"] == 2
    assert ver["mismatch_count"] == 0
    assert ver["state_vector"].lifecycle == OperationalLifecycle.NORMAL


def test_airgap_bundle_tamper_detection(tmp_path):
    """Tampered files within an airgap bundle must be detected and quarantined."""
    import io
    import tarfile

    # Create original bundle
    orig_file = tmp_path / "original.txt"
    orig_file.write_text("authentic data")
    bundle_path = tmp_path / "bundle.tar.gz"
    AirgapPackager.create_bundle("tamper-test", [orig_file], bundle_path)

    # Read manifest from bundle
    with tarfile.open(bundle_path, "r:gz") as tar:
        extracted = tar.extractfile("bundle_manifest.json")
        assert extracted is not None
        manifest_bytes = extracted.read()

    # Create tampered bundle keeping old manifest but changing payload
    tampered_bundle = tmp_path / "tampered.tar.gz"
    with tarfile.open(tampered_bundle, "w:gz") as tar:
        # Add original manifest
        t_info = tarfile.TarInfo(name="bundle_manifest.json")
        t_info.size = len(manifest_bytes)
        tar.addfile(t_info, io.BytesIO(manifest_bytes))

        # Add corrupt payload
        corrupt_bytes = b"malicious tampered content"
        p_info = tarfile.TarInfo(name=f"payload/{orig_file}")
        p_info.size = len(corrupt_bytes)
        tar.addfile(p_info, io.BytesIO(corrupt_bytes))

    # Verification must fail
    ver = AirgapPackager.verify_bundle(tampered_bundle)
    assert ver["valid"] is False
    assert ver["mismatch_count"] == 1
    assert ver["state_vector"].lifecycle == OperationalLifecycle.QUARANTINED
