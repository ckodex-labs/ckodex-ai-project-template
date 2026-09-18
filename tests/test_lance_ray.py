"""
Tests for Distributed Lance-Ray Engine adapter.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest
import ray

from ckodex_aiops.adapters.ray.lance_ray import LanceRayEngine
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager


@pytest.fixture(scope="module", autouse=True)
def init_ray():
    RayRuntimeManager.initialize()


def test_lance_ray_write_and_read(tmp_path: Path):
    table = pa.Table.from_arrays(
        [
            pa.array([1, 2, 3, 4, 5]),
            pa.array(["a", "b", "c", "d", "e"]),
            pa.array([10.0, 20.0, 30.0, 40.0, 50.0]),
        ],
        names=["id", "name", "val"],
    )
    ray_ds = ray.data.from_arrow(table)
    target_uri = str(tmp_path / "lance_ray_test.lance")

    # 1. Write via LanceRayEngine
    LanceRayEngine.write(ray_ds, target_uri, mode="overwrite")

    # 2. Read back with projection and predicate pushdown
    read_ds = LanceRayEngine.read(
        target_uri,
        columns=["id", "val"],
        filter_expr="val > 25.0",
    )

    batches = read_ds.take_all()
    assert len(batches) == 3
    vals = [b["val"] for b in batches]
    assert sorted(vals) == [30.0, 40.0, 50.0]


def test_lance_ray_evolve_columns(tmp_path: Path):
    table = pa.Table.from_arrays(
        [
            pa.array([101, 102, 103]),
            pa.array([1.5, 2.5, 3.5]),
        ],
        names=["id", "sensor_reading"],
    )
    ray_ds = ray.data.from_arrow(table)
    target_uri = str(tmp_path / "evolve_test.lance")

    LanceRayEngine.write(ray_ds, target_uri, mode="overwrite")

    # Column evolution transform function
    def add_calibrated_col(batch: pa.RecordBatch) -> pa.RecordBatch:
        sensor = batch["sensor_reading"].to_numpy()
        calibrated = sensor * 2.0
        return pa.RecordBatch.from_arrays(
            [pa.array(calibrated, type=pa.float64())],
            names=["calibrated_reading"],
        )

    LanceRayEngine.evolve_columns(target_uri, add_calibrated_col)

    # Read back and verify the column exists
    evolved_ds = LanceRayEngine.read(target_uri)
    all_rows = evolved_ds.take_all()
    assert len(all_rows) == 3
    assert "calibrated_reading" in all_rows[0]
    assert all_rows[0]["calibrated_reading"] == pytest.approx(3.0)


def test_lance_ray_compact(tmp_path: Path):
    table = pa.Table.from_arrays(
        [pa.array(list(range(200)))],
        names=["seq"],
    )
    target_uri = str(tmp_path / "compact_test.lance")

    # Write in multiple tiny batches to force multiple fragments
    ray_ds = ray.data.from_arrow(table)
    LanceRayEngine.write(
        ray_ds, target_uri, mode="overwrite", min_rows_per_file=10, max_rows_per_file=50
    )

    # Compact files
    LanceRayEngine.compact(target_uri, target_rows_per_fragment=200)

    import lance

    ds = lance.dataset(target_uri)
    assert ds.count_rows() == 200
