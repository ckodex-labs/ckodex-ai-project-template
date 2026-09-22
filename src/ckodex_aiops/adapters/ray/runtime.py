"""
Resilient Ray Runtime Manager.
Handles cluster discovery, local fallback, health telemetry, and state vector reporting.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import ray
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)


class RayRuntimeManager:
    """
    Manages Ray cluster lifecycle, addressing quirks, and health diagnostics.
    """

    DEFAULT_LOCAL_CPUS = 2
    DEFAULT_LOCAL_MEMORY_GB = 4.0
    DEFAULT_LOCAL_OBJECT_STORE_GB = 2.0

    @classmethod
    def initialize(
        cls,
        address: str | None = "auto",
        num_cpus: int | None = None,
        max_memory_gb: float | None = None,
        object_store_gb: float | None = None,
        ignore_reinit_error: bool = True,
        runtime_env: dict[str, Any] | None = None,
    ) -> bool:
        """
        Safely initialize Ray cluster connection with strict resource bounding (Rule #31).
        Does not claim the host's entire physical RAM. Bounded to conservative defaults locally.
        """
        if ray.is_initialized():
            return True

        # Unconditionally sanitize invalid RAY_ADDRESS in ambient environment
        ambient_env_addr = os.environ.get("RAY_ADDRESS", "").strip()
        if ambient_env_addr.startswith("http://") or ambient_env_addr.startswith("https://"):
            os.environ.pop("RAY_ADDRESS", None)

        # Parse address candidates: explicit address, RAY_ADDRESS, or auto
        target_address = address
        if target_address == "auto":
            env_addr = os.environ.get("RAY_ADDRESS", "").strip()
            if env_addr and not (env_addr.startswith("http://") or env_addr.startswith("https://")):
                target_address = env_addr
            else:
                target_address = None
        elif target_address and (
            target_address.startswith("http://") or target_address.startswith("https://")
        ):
            target_address = None

        # Compute conservative memory bounds for local cluster (Rule #31: Resilience must be bounded)
        mem_bytes = int((max_memory_gb or cls.DEFAULT_LOCAL_MEMORY_GB) * (1024**3))
        obj_store_bytes = int((object_store_gb or cls.DEFAULT_LOCAL_OBJECT_STORE_GB) * (1024**3))

        # Disable Ray's automatic uv run working_dir packager to prevent broken worker venvs in containerized CI
        os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"
        try:
            import ray._private.ray_constants as _ray_constants

            _ray_constants.RAY_ENABLE_UV_RUN_RUNTIME_ENV = False
        except Exception:
            pass

        # 1. Attempt connection to target remote address (if provided)
        if target_address:
            try:
                ray.init(
                    address=target_address,
                    ignore_reinit_error=ignore_reinit_error,
                    runtime_env=runtime_env or {},
                    logging_level=logging.WARNING,
                )
                return True
            except Exception:
                pass  # Fall back to local below

        # 2. Attempt connection to local existing Ray instance (address="auto")
        try:
            ray.init(
                address="auto",
                ignore_reinit_error=ignore_reinit_error,
                runtime_env=runtime_env or {},
                logging_level=logging.WARNING,
            )
            return True
        except Exception:
            pass

        # 3. Fallback: Spin up an embedded local Ray cluster bounded to conservative limits
        try:
            ray.init(
                address=None,
                num_cpus=num_cpus or cls.DEFAULT_LOCAL_CPUS,
                _memory=mem_bytes,
                object_store_memory=obj_store_bytes,
                ignore_reinit_error=True,
                runtime_env=runtime_env or {},
                logging_level=logging.WARNING,
            )
            return True
        except Exception:
            # Fallback without explicit memory kwargs if older Ray runtime
            try:
                ray.init(
                    address=None,
                    num_cpus=num_cpus or cls.DEFAULT_LOCAL_CPUS,
                    ignore_reinit_error=True,
                    runtime_env=runtime_env or {},
                    logging_level=logging.WARNING,
                )
                return True
            except Exception:
                return False

    @classmethod
    def shutdown(cls) -> None:
        if ray.is_initialized():
            ray.shutdown()

    @classmethod
    def get_cluster_info(cls) -> dict[str, Any]:
        if not ray.is_initialized():
            return {"status": "NOT_INITIALIZED", "nodes": 0, "cpus": 0, "gpus": 0}

        resources = ray.cluster_resources()
        nodes = ray.nodes()

        # Determine if running local embedded cluster or connected to remote
        is_local = any(n.get("NodeManagerAddress") in ("127.0.0.1", "localhost") for n in nodes)

        return {
            "status": "ONLINE",
            "mode": "LOCAL_EMBEDDED" if is_local else "REMOTE_CLUSTER",
            "nodes": len(nodes),
            "cpus": resources.get("CPU", 0.0),
            "gpus": resources.get("GPU", 0.0),
            "allocated_memory_gb": round(resources.get("memory", 0.0) / (1024**3), 2),
            "memory_gb": round(resources.get("memory", 0.0) / (1024**3), 2),
            "object_store_gb": round(resources.get("object_store_memory", 0.0) / (1024**3), 2),
            "active_nodes": [n.get("NodeManagerAddress") for n in nodes if n.get("Alive")],
        }

    @classmethod
    def health_check(cls) -> StateVector:
        if not ray.is_initialized():
            return StateVector(
                presence=Presence.EMPTY,
                valence=Valence.NEGATIVE,
                anti=Anti.CONTRADICTS,
                coherence=Coherence.DECOHERENT,
                evidence=EvidenceStatus.OBSERVED,
                lifecycle=OperationalLifecycle.FAILED,
                metadata={"reason": "Ray cluster is not initialized."},
            )

        info = cls.get_cluster_info()
        cpus = info.get("cpus", 0.0)
        if cpus < 1.0:
            return StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEGATIVE,
                anti=Anti.CONTRADICTS,
                coherence=Coherence.PARTIALLY_COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.DEGRADED,
                metadata={"reason": "Zero active CPUs detected in Ray cluster.", "info": info},
            )

        return StateVector(
            presence=Presence.PRESENT,
            valence=Valence.POSITIVE,
            anti=Anti.NONE,
            coherence=Coherence.COHERENT,
            evidence=EvidenceStatus.VERIFIED,
            lifecycle=OperationalLifecycle.NORMAL,
            metadata=info,
        )
