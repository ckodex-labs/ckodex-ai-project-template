"""
Ray Placement Group & Topology Management (CKODEX Rule #9 & #25).
Provides atomic gang scheduling, GPU/CPU bundle reservations, and
heterogeneous cluster topology management using Ray placement groups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import ray
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager
from ray.util.placement_group import (
    PlacementGroup,
    placement_group,
    placement_group_table,
    remove_placement_group,
)


@dataclass(frozen=True)
class PlacementGroupSpec:
    """Specification of an atomic placement group reservation."""

    name: str
    strategy: Literal["STRICT_SPREAD", "SPREAD", "STRICT_PACK", "PACK"]
    bundles: list[dict[str, float | int]]
    timeout_seconds: float = 30.0


class RayPlacementGroupManager:
    """
    Manages allocation, scheduling, and cleanup of Ray placement groups.
    Ensures gang scheduling for multi-worker PyTorch and Ray actor pools.
    """

    @classmethod
    def create_placement_group(
        cls,
        spec: PlacementGroupSpec,
    ) -> PlacementGroup:
        """
        Atomically allocates a placement group according to the resource specification.
        """
        RayRuntimeManager.initialize()

        pg = placement_group(
            bundles=spec.bundles,
            strategy=spec.strategy,
            name=spec.name,
            lifetime="detached",
        )

        ready = ray.get(pg.ready(), timeout=spec.timeout_seconds)
        if not ready:
            remove_placement_group(pg)
            raise TimeoutError(
                f"Placement group '{spec.name}' failed to be scheduled within {spec.timeout_seconds}s."
            )

        return pg

    @classmethod
    def create_inference_placement_group(
        cls,
        name: str = "inference_pool_pg",
        num_actors: int = 2,
        cpus_per_actor: int = 1,
        gpus_per_actor: float = 0.0,
        strategy: Literal["STRICT_SPREAD", "SPREAD", "STRICT_PACK", "PACK"] = "PACK",
    ) -> PlacementGroup:
        """
        Helper to allocate balanced compute bundles for model inference actors.
        """
        bundle: dict[str, float | int] = {"CPU": cpus_per_actor}
        if gpus_per_actor > 0:
            bundle["GPU"] = gpus_per_actor

        bundles = [bundle.copy() for _ in range(num_actors)]
        spec = PlacementGroupSpec(name=name, strategy=strategy, bundles=bundles)
        return cls.create_placement_group(spec)

    @classmethod
    def list_placement_groups(cls) -> list[dict[str, Any]]:
        """
        Lists all active placement groups in the Ray cluster.
        """
        RayRuntimeManager.initialize()
        pgs = placement_group_table()
        results = []
        for pg_id, pg_info in pgs.items():
            results.append(
                {
                    "placement_group_id": pg_id,
                    "name": pg_info.get("name", "unnamed"),
                    "state": pg_info.get("state", "UNKNOWN"),
                    "strategy": pg_info.get("strategy", "UNKNOWN"),
                    "bundles": pg_info.get("bundles", []),
                }
            )
        return results

    @classmethod
    def remove_placement_group(cls, pg: PlacementGroup) -> None:
        """Removes and deallocates a placement group."""
        remove_placement_group(pg)
