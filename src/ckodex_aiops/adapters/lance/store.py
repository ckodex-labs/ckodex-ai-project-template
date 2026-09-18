"""
Lance and LanceDB Vector Store Adapter.
Provides high-performance vector indexing, hybrid search, and PyArrow zero-copy export.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import lancedb
import numpy as np
import polars as pl
import pyarrow as pa


class LanceVectorStore:
    """
    LanceDB high-level vector database adapter.
    """

    def __init__(self, db_uri: str | Path) -> None:
        self.db_uri = Path(db_uri)
        self.db_uri.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(self.db_uri))

    def create_or_replace_table(
        self,
        table_name: str,
        data: pl.DataFrame | pa.Table,
    ) -> lancedb.table.Table:
        """Create or overwrite a table with vector embeddings."""
        if isinstance(data, pl.DataFrame):
            arrow_data = data.to_arrow()
        else:
            arrow_data = data

        return self._db.create_table(
            name=table_name,
            data=arrow_data,
            mode="overwrite",
        )

    def open_table(self, table_name: str) -> lancedb.table.Table:
        return self._db.open_table(table_name)

    def search_vectors(
        self,
        table_name: str,
        query_vector: list[float] | np.ndarray,
        limit: int = 10,
        filter_expr: str | None = None,
        select_columns: list[str] | None = None,
    ) -> pl.DataFrame:
        """
        Execute vector similarity search returning a Polars DataFrame.
        """
        table = self.open_table(table_name)
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()

        search_query = table.search(query_vector).limit(limit)
        if filter_expr:
            search_query = search_query.where(filter_expr)
        if select_columns:
            search_query = search_query.select(select_columns)

        arrow_result = search_query.to_arrow()
        return pl.from_arrow(arrow_result)  # type: ignore[return-value]

    def list_tables(self) -> list[str]:
        return list(self._db.table_names())

    def get_table_metadata(self, table_name: str) -> dict[str, Any]:
        table = self.open_table(table_name)
        return {
            "name": table_name,
            "version": table.version,
            "schema": [f"{f.name}: {f.type}" for f in table.schema],
            "num_rows": table.count_rows(),
        }
