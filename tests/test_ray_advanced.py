"""Tests for Ray Ecosystem & Lance Advanced Parallelism Best Practices.
Validates Ray Placement Groups, fault-tolerant pools, Plasma zero-copy dispatching,
and Lance full lifecycle table optimization.
"""

from __future__ import annotations

from ckodex_aiops.adapters.ray.actors.pool import ActorPoolManager
from ckodex_aiops.adapters.ray.lance_ray import LanceRayEngine
from ckodex_aiops.adapters.ray.placement import PlacementGroupSpec, RayPlacementGroupManager
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager


def test_ray_placement_group_lifecycle():
    """Validates atomic allocation, listing, and removal of Ray placement groups."""
    RayRuntimeManager.initialize()

    spec = PlacementGroupSpec(
        name="test_pg_gang",
        strategy="PACK",
        bundles=[{"CPU": 1}, {"CPU": 1}],
        timeout_seconds=10.0,
    )

    pg = RayPlacementGroupManager.create_placement_group(spec)
    assert pg is not None

    pg_list = RayPlacementGroupManager.list_placement_groups()
    assert any(p["name"] == "test_pg_gang" for p in pg_list)

    # Cleanup
    RayPlacementGroupManager.remove_placement_group(pg)


def test_actor_pool_with_placement_group():
    """Validates scheduling actors onto Ray placement groups."""
    RayRuntimeManager.initialize()

    pg = RayPlacementGroupManager.create_inference_placement_group(
        name="test_infer_pg",
        num_actors=2,
        cpus_per_actor=1,
        strategy="PACK",
    )

    try:
        pool = ActorPoolManager.create_inference_pool_with_placement_group(
            size=2,
            input_dim=16,
            hidden_dim=32,
            num_classes=3,
            placement_group=pg,
        )

        health = pool.health_check()
        assert len(health) == 2
        assert all(h["status"] == "HEALTHY" for h in health)
        pool.terminate()
    finally:
        RayPlacementGroupManager.remove_placement_group(pg)


def test_zero_copy_plasma_shared_batch_dispatch():
    """Validates dispatching ObjectRefs directly from Plasma store without redundant driver copies."""
    RayRuntimeManager.initialize()

    pool = ActorPoolManager.create_embedding_pool(size=2, embedding_dim=16)
    batches = [
        [[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i] for i in range(10)],
        [[0.5 * i, 0.6 * i, 0.7 * i, 0.8 * i] for i in range(10)],
    ]

    results = pool.dispatch_shared_batches("generate_embeddings", batches)
    assert len(results) == 2
    assert len(results[0]) == 10
    assert len(results[1]) == 10
    pool.terminate()


def test_lance_ray_full_optimize(tmp_path):
    """Validates full lifecycle optimization: fragment compaction + old version cleanup."""
    import lance
    import pyarrow as pa

    RayRuntimeManager.initialize()

    # Create dataset with multiple small fragments
    table_path = tmp_path / "optimize_test.lance"
    schema = pa.schema([("id", pa.int64()), ("val", pa.float64())])

    # Write 3 separate appends to create 3 fragments
    for i in range(3):
        t = pa.Table.from_arrays(
            [pa.array([i * 10 + j for j in range(10)]), pa.array([float(j) for j in range(10)])],
            schema=schema,
        )
        if i == 0:
            lance.write_dataset(t, str(table_path), mode="overwrite")
        else:
            lance.write_dataset(t, str(table_path), mode="append")

    ds_initial = lance.dataset(str(table_path))
    assert len(ds_initial.get_fragments()) >= 2

    # Execute full lifecycle optimization
    opt_report = LanceRayEngine.optimize(
        table_path, target_rows_per_fragment=1000, cleanup_older_than_days=0
    )
    assert "fragments_before" in opt_report
    assert "fragments_after" in opt_report
    assert opt_report["total_rows"] == 30
