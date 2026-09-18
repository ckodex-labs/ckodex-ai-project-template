"""
Unit tests for Kedro LanceDataSet.
"""

import numpy as np
import polars as pl

from ckodex_aiops.datasets.lance_dataset import LanceDataSet


def test_lance_dataset_save_load(temp_workspace, sample_dataframe):
    target_path = temp_workspace / "events.lance"
    dataset = LanceDataSet(filepath=str(target_path), mode="overwrite")

    # Save
    dataset.save(sample_dataframe)
    assert target_path.exists()

    # Load
    loaded_df = dataset.load()
    assert isinstance(loaded_df, pl.DataFrame)
    assert loaded_df.height == sample_dataframe.height
    assert set(loaded_df.columns) == set(sample_dataframe.columns)


def test_lance_dataset_projections_and_limits(temp_workspace, sample_dataframe):
    target_path = temp_workspace / "projected.lance"
    dataset_write = LanceDataSet(filepath=str(target_path), mode="overwrite")
    dataset_write.save(sample_dataframe)

    # Load with projection and limit
    dataset_read = LanceDataSet(
        filepath=str(target_path),
        columns=["id", "feature_a"],
        limit=25,
    )
    df = dataset_read.load()
    assert df.height == 25
    assert df.columns == ["id", "feature_a"]


def test_lance_dataset_vector_indexing(temp_workspace):
    target_path = temp_workspace / "vectors.lance"
    n = 64
    np.random.seed(42)
    df = pl.DataFrame(
        {
            "id": [f"v_{i}" for i in range(n)],
            "vector": [np.random.randn(16).astype(np.float32).tolist() for i in range(n)],
            "target_class": [i % 2 for i in range(n)],
        }
    )

    dataset = LanceDataSet(
        filepath=str(target_path),
        vector_index_column="vector",
        vector_metric="cosine",
        num_partitions=2,
        num_sub_vectors=2,
    )
    dataset.save(df)

    # Validate underlying Lance dataset
    ds = dataset.get_dataset()
    assert ds.count_rows() == n
    loaded = dataset.load()
    assert loaded.height == n
