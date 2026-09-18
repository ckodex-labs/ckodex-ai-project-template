"""
Distributed Lance-Ray Engine Adapter.
Provides distributed ETL, fragment writing, zero-driver-OOM column evolution,
compaction, and vector indexing using lance-ray and Ray Data.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

import lance
import lance_ray
import pyarrow as pa

import ray
import ray.data
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager


class LanceRayEngine:
    """
    High-assurance Ray distributed processing adapter for Lance datasets.
    """

    @classmethod
    def read(
        cls,
        uri: str | Path,
        columns: list[str] | None = None,
        filter_expr: str | None = None,
        batch_size: int = 1024,
        batch_readahead: int = 4,
        with_metadata: bool = False,
    ) -> ray.data.Dataset:
        """
        Reads a Lance dataset into a distributed Ray Dataset with predicate and projection pushdown.
        """
        RayRuntimeManager.initialize()
        return lance_ray.read_lance(
            str(uri),
            columns=columns,
            filter=filter_expr,
            scanner_options={
                "batch_size": batch_size,
                "batch_readahead": batch_readahead,
            },
            with_metadata=with_metadata,
        )

    @classmethod
    def write(
        cls,
        dataset: ray.data.Dataset,
        uri: str | Path,
        mode: Literal["create", "overwrite", "append"] = "overwrite",
        stream: bool = False,
        enable_stable_row_ids: bool = True,
        min_rows_per_file: int = 10,
        max_rows_per_file: int = 1_000_000,
    ) -> None:
        """
        Writes a distributed Ray Dataset into Lance storage using fast-path or streaming fragments.
        """
        RayRuntimeManager.initialize()
        Path(uri).parent.mkdir(parents=True, exist_ok=True)
        # Ensure min_rows_per_file <= max_rows_per_file
        min_rows = min(min_rows_per_file, max_rows_per_file)
        lance_ray.write_lance(
            dataset,
            str(uri),
            mode=mode,
            stream=stream,
            enable_stable_row_ids=enable_stable_row_ids,
            min_rows_per_file=min_rows,
            max_rows_per_file=max_rows_per_file,
        )

    @classmethod
    def evolve_columns(
        cls,
        uri: str | Path,
        transform_fn: Callable[[pa.Table], pa.Table],
    ) -> None:
        """
        Performs in-place distributed column evolution (e.g. backfilling embeddings or flags)
        without driver OOM using lance-ray add_columns.
        """
        RayRuntimeManager.initialize()
        lance_ray.add_columns(
            str(uri),
            transform=transform_fn,
        )

    @classmethod
    def create_distributed_vector_index(
        cls,
        uri: str | Path,
        column: str = "vector",
        index_type: Literal["IVF_PQ", "IVF_HNSW_PQ", "IVF_RQ"] = "IVF_PQ",
        metric: Literal["cosine", "l2", "dot"] = "cosine",
        num_partitions: int = 4,
        num_sub_vectors: int = 2,
    ) -> None:
        """
        Builds vector indices distributed across Ray workers.
        """
        RayRuntimeManager.initialize()
        ds = lance.dataset(str(uri))
        if column in ds.schema.names and ds.count_rows() > 0:
            try:
                lance_ray.create_index(
                    str(uri),
                    column=column,
                    index_type=index_type,
                    metric=metric,
                    num_partitions=num_partitions,
                    num_sub_vectors=num_sub_vectors,
                    replace=True,
                )
            except Exception:
                # Fallback to local index creation if dataset size is below Ray partition threshold
                ds.create_index(
                    metric=metric,
                    vector_column_name=column,
                    index_type="IVF_PQ",
                    num_partitions=num_partitions,
                    num_sub_vectors=num_sub_vectors,
                    replace=True,
                )

    @classmethod
    def compact(
        cls,
        uri: str | Path,
        target_rows_per_fragment: int = 100_000,
    ) -> None:
        """
        Executes distributed fragment compaction on Ray to optimize read IOPS and eliminate fragmentation.
        """
        RayRuntimeManager.initialize()
        try:
            lance_ray.compact_files(
                str(uri),
                target_rows_per_fragment=target_rows_per_fragment,
            )
        except Exception:
            ds = lance.dataset(str(uri))
            ds.optimize.compact_files(target_rows_per_fragment=target_rows_per_fragment)
