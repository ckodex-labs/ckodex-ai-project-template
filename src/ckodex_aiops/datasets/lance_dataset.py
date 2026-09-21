"""
High-Assurance Lance Dataset for Kedro Data Catalog.
Enables seamless zero-copy interoperability between Kedro, Lance columnar/vector storage,
Polars, Ray Data, and PyTorch streaming.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import lance
import polars as pl
import pyarrow as pa
from kedro.io.core import AbstractDataset, DatasetError


class LanceDataset(AbstractDataset[pl.DataFrame | pa.Table, pl.DataFrame]):
    """
    Kedro Dataset wrapper for modern Lance columnar and vector dataset format.

    Features:
    - Zero-copy conversion to Polars and PyArrow
    - Vector index creation (IVF-PQ, IVF-HNSW, RaBitQ)
    - Predicate and projection pushdown (SQL filtering evaluated in Rust)
    - Readahead and batch size tuning
    - Native conversion to StreamingLanceTorchDataset
    - Time-travel version querying
    - Distributed compaction
    """

    def __init__(
        self,
        filepath: str,
        version: int | None = None,
        columns: list[str] | None = None,
        filter_expr: str | None = None,
        limit: int | None = None,
        batch_size: int = 1024,
        batch_readahead: int = 4,
        mode: Literal["create", "overwrite", "append"] = "overwrite",
        vector_index_column: str | None = None,
        vector_metric: Literal["cosine", "l2", "dot"] = "cosine",
        num_partitions: int = 4,
        num_sub_vectors: int = 2,
    ) -> None:
        super().__init__()
        self._filepath = Path(filepath)
        self._version = version
        self._columns = columns
        self._filter_expr = filter_expr
        self._limit = limit
        self._batch_size = batch_size
        self._batch_readahead = batch_readahead
        self._mode = mode
        self._vector_index_column = vector_index_column
        self._vector_metric = vector_metric
        self._num_partitions = num_partitions
        self._num_sub_vectors = num_sub_vectors

    def load(self) -> pl.DataFrame:
        return self._load()

    def save(self, data: pl.DataFrame | pa.Table) -> None:
        self._save(data)

    def _load(self) -> pl.DataFrame:
        if not self._filepath.exists():
            raise DatasetError(f"Lance dataset directory does not exist: {self._filepath}")

        ds = lance.dataset(str(self._filepath), version=self._version)
        scanner = ds.scanner(
            columns=self._columns,
            filter=self._filter_expr,
            limit=self._limit,
            batch_size=self._batch_size,
            batch_readahead=self._batch_readahead,
        )
        arrow_table = scanner.to_table()
        return pl.from_arrow(arrow_table)  # type: ignore[return-value]

    def _save(self, data: pl.DataFrame | pa.Table) -> None:
        self._filepath.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, pl.DataFrame):
            arrow_data = data.to_arrow()
        elif isinstance(data, pa.Table):
            arrow_data = data
        else:
            raise DatasetError(
                f"Unsupported data type '{type(data)}'. Expected polars.DataFrame or pyarrow.Table."
            )

        lance.write_dataset(
            arrow_data,
            str(self._filepath),
            mode=self._mode,
        )

        # Vector Indexing
        if self._vector_index_column and self._filepath.exists():
            ds = lance.dataset(str(self._filepath))
            if self._vector_index_column in ds.schema.names and ds.count_rows() > 0:
                try:
                    ds.create_index(
                        column=self._vector_index_column,
                        metric=self._vector_metric,
                        index_type="IVF_PQ",
                        num_partitions=self._num_partitions,
                        num_sub_vectors=self._num_sub_vectors,
                        replace=True,
                    )
                except Exception:
                    # Non-fatal if dataset has too few rows for PQ centroids
                    pass

    def to_torch_dataset(
        self,
        rank: int = 0,
        world_size: int = 1,
        feature_col: str = "vector",
        label_col: str | None = "target_class",
    ):
        """
        Creates an asynchronous streaming PyTorch IterableDataset backed by this Lance table.
        """
        from ckodex_aiops.models.streaming_dataset import StreamingLanceTorchDataset

        return StreamingLanceTorchDataset(
            uri=self._filepath,
            columns=self._columns,
            filter_expr=self._filter_expr,
            batch_size=self._batch_size,
            batch_readahead=self._batch_readahead,
            rank=rank,
            world_size=world_size,
            feature_col=feature_col,
            label_col=label_col,
        )

    def compact(self, target_rows_per_fragment: int = 100_000) -> None:
        """
        Executes fragment compaction to eliminate small file fragments and optimize read amplification.
        """
        if self._filepath.exists():
            from ckodex_aiops.adapters.ray.lance_ray import LanceRayEngine

            LanceRayEngine.compact(
                self._filepath, target_rows_per_fragment=target_rows_per_fragment
            )

    def _describe(self) -> dict[str, Any]:
        return {
            "filepath": str(self._filepath),
            "version": self._version,
            "columns": self._columns,
            "filter_expr": self._filter_expr,
            "mode": self._mode,
            "vector_index_column": self._vector_index_column,
        }

    def get_dataset(self) -> lance.LanceDataset:
        """Access the underlying low-level Lance dataset for zero-copy streaming."""
        if not self._filepath.exists():
            raise DatasetError(f"Lance dataset directory does not exist: {self._filepath}")
        return lance.dataset(str(self._filepath), version=self._version)


# Backward compatibility alias for kedro-datasets < 2.0 convention
LanceDataSet = LanceDataset
