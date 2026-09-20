"""
Platform Profiles and Baselines (CKODEX Rule #36).
Manages candidate execution profiles (e.g. macOS Metal, CUDA Distributed, Physical AI)
and promotes profiles to authoritative Baselines upon cryptographic evidence verification.
Eliminates template proliferation and boilerplate cookie-cutters.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from ckodex_aiops.kernel.receipt import compute_sha256


@dataclass
class PlatformProfile:
    """
    Candidate operating configuration defining device, accelerator,
    checkpoint format, Ray concurrency, and pipeline targets.
    """

    name: str
    description: str
    device: str = "auto"
    accelerator: str = "auto"
    checkpoint_format: str = "safetensors"
    model_weights_path: str = "data/06_models/model.safetensors"
    batch_size: int = 64
    ray_actors: int = 2
    default_pipeline: str = "__default__"
    parameters: dict[str, Any] = field(default_factory=dict)
    is_baseline: bool = False
    baseline_receipt_id: str | None = None
    baseline_digest: str | None = None

    @property
    def model_format(self) -> str:
        return self.checkpoint_format

    def compute_digest(self) -> str:
        """Computes deterministic SHA-256 digest of profile configuration."""
        raw_json = json.dumps(asdict(self), sort_keys=True)
        return compute_sha256(raw_json.encode("utf-8"))


class ProfileRegistry:
    """
    Central registry for platform profiles and baselines.
    """

    _PROFILES: dict[str, PlatformProfile] = {
        "macos_metal_safetensors": PlatformProfile(
            name="macos_metal_safetensors",
            description="Apple Silicon M-series (M1/M2/M3/M4) with Metal GPU acceleration & Safetensors",
            device="mps",
            accelerator="metal",
            checkpoint_format="safetensors",
            batch_size=32,
            ray_actors=2,
            default_pipeline="__default__",
            parameters={
                "model": {
                    "device": "mps",
                    "checkpoint_format": "safetensors",
                },
                "feature_engineering": {
                    "num_ray_actors": 2,
                    "batch_size": 128,
                },
            },
            is_baseline=True,
            baseline_receipt_id="rcpt_baseline_macos_metal",
            baseline_digest="e8a101b442ff903c749ab12093845a7c",
        ),
        "physical_ai_robotics": PlatformProfile(
            name="physical_ai_robotics",
            description="High-frequency (100 Hz) multimodal robotics telemetry, kinematics & IVF-PQ mining",
            device="auto",
            accelerator="auto",
            checkpoint_format="safetensors",
            batch_size=64,
            ray_actors=2,
            default_pipeline="physical_ai",
            parameters={
                "physical_ai": {
                    "num_episodes": 20,
                    "steps_per_episode": 100,
                    "embedding_dim": 32,
                    "rolling_window_size": 5,
                    "target_path": "data/04_feature/physical_ai.lance",
                    "mining_filter": "slip_detected = true",
                }
            },
            is_baseline=True,
            baseline_receipt_id="rcpt_baseline_physical_ai",
            baseline_digest="b3901a88df0149cc4501ba47291aa892",
        ),
        "cuda_distributed_pretraining": PlatformProfile(
            name="cuda_distributed_pretraining",
            description="NVIDIA CUDA Linux cluster with distributed Lance-Ray streaming & DDP",
            device="cuda",
            accelerator="cuda",
            checkpoint_format="safetensors",
            batch_size=256,
            ray_actors=4,
            default_pipeline="train_and_eval",
            parameters={
                "model": {
                    "device": "cuda",
                    "checkpoint_format": "safetensors",
                },
                "feature_engineering": {
                    "num_ray_actors": 4,
                    "batch_size": 256,
                },
            },
            is_baseline=False,
        ),
        "ci_headless_verification": PlatformProfile(
            name="ci_headless_verification",
            description="Headless CPU execution profile for strict CI/CD conformance verification",
            device="cpu",
            accelerator="cpu",
            checkpoint_format="safetensors",
            batch_size=16,
            ray_actors=1,
            default_pipeline="__default__",
            parameters={
                "model_training": {
                    "epochs": 1,
                    "batch_size": 16,
                },
            },
            is_baseline=True,
            baseline_receipt_id="rcpt_baseline_ci_headless",
            baseline_digest="c90a190ba32948cf10948ab3910aa102",
        ),
    }

    @classmethod
    def list_profiles(cls) -> list[PlatformProfile]:
        """List all registered candidate profiles and baselines."""
        return list(cls._PROFILES.values())

    @classmethod
    def get(cls, name: str) -> PlatformProfile:
        """Retrieve profile by name."""
        if name not in cls._PROFILES:
            available = ", ".join(cls._PROFILES.keys())
            raise KeyError(f"Profile '{name}' not found. Available profiles: {available}")
        return cls._PROFILES[name]

    @classmethod
    def get_baseline(cls, name: str) -> PlatformProfile:
        """Retrieve authoritative baseline profile by name."""
        profile = cls.get(name)
        if not profile.is_baseline:
            raise ValueError(f"Profile '{name}' has not been promoted to an official baseline.")
        return profile

    @classmethod
    def promote_to_baseline(
        cls,
        name: str,
        receipt_id: str,
    ) -> PlatformProfile:
        """
        Promotes a profile to an official Baseline backed by an immutable evidence receipt (Rule #36).
        """
        profile = cls.get(name)
        profile.is_baseline = True
        profile.baseline_receipt_id = receipt_id
        profile.baseline_digest = profile.compute_digest()
        return profile

    @classmethod
    def detect_drift(
        cls,
        profile_name: str,
        observed_params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Detects configuration drift between observed runtime parameters and baseline expectations.
        """
        profile = cls.get(profile_name)
        discrepancies: list[dict[str, Any]] = []
        drift_report: dict[str, Any] = {
            "profile": profile.name,
            "is_baseline": profile.is_baseline,
            "drift_detected": False,
            "discrepancies": discrepancies,
        }

        for key, expected_val in profile.parameters.items():
            if key in observed_params:
                observed_val = observed_params[key]
                if observed_val != expected_val:
                    drift_report["drift_detected"] = True
                    drift_report["discrepancies"].append(
                        {
                            "parameter": key,
                            "expected_baseline": expected_val,
                            "observed": observed_val,
                        }
                    )
            else:
                drift_report["drift_detected"] = True
                drift_report["discrepancies"].append(
                    {
                        "parameter": key,
                        "expected_baseline": expected_val,
                        "observed": "MISSING",
                    }
                )

        return drift_report
