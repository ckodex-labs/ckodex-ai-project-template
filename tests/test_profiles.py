"""
Tests for Platform Profiles and Baselines (Rule #36).
"""

from __future__ import annotations

from ckodex_aiops.kernel.profiles import ProfileRegistry


def test_profile_registry_list_and_get():
    profiles = ProfileRegistry.list_profiles()
    assert len(profiles) >= 3

    names = [p.name for p in profiles]
    assert "macos_metal_safetensors" in names
    assert "physical_ai_robotics" in names
    assert "ci_headless_verification" in names

    metal_prof = ProfileRegistry.get("macos_metal_safetensors")
    assert metal_prof.device == "mps"
    assert metal_prof.accelerator == "metal"
    assert metal_prof.checkpoint_format == "safetensors"
    assert metal_prof.is_baseline is True


def test_profile_promotion_to_baseline():
    prof = ProfileRegistry.get("cuda_distributed_pretraining")
    assert prof.is_baseline is False

    promoted = ProfileRegistry.promote_to_baseline(
        "cuda_distributed_pretraining", receipt_id="rcpt_cuda_verified_01"
    )
    assert promoted.is_baseline is True
    assert promoted.baseline_receipt_id == "rcpt_cuda_verified_01"
    assert promoted.baseline_digest is not None


def test_drift_detection():
    # Matching params -> no drift
    profile = ProfileRegistry.get("macos_metal_safetensors")
    observed = dict(profile.parameters)
    drift = ProfileRegistry.detect_drift("macos_metal_safetensors", observed)
    assert drift["drift_detected"] is False
    assert len(drift["discrepancies"]) == 0

    # Altered params -> drift detected
    altered = {"model": {"device": "cpu", "checkpoint_format": "pt"}}
    drift = ProfileRegistry.detect_drift("macos_metal_safetensors", altered)
    assert drift["drift_detected"] is True
    assert len(drift["discrepancies"]) > 0
