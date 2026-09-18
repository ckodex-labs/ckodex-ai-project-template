"""
Data Ingestion Pipeline Nodes.
Generates, validates, and admits raw event data into Lance storage using Polars.
"""

from __future__ import annotations

import time

import numpy as np
import polars as pl

from ckodex_aiops.kernel.domain import DatasetContract
from ckodex_aiops.validation.validators import DataContractValidator


def generate_synthetic_telemetry(num_records: int = 1000) -> pl.DataFrame:
    """
    Generate synthetic high-throughput telemetry records using Polars.
    """
    np.random.seed(42)
    categories = ["compute", "network", "storage", "database"]

    ids = [f"rec_{i:06d}" for i in range(num_records)]
    timestamps = [time.time() - (num_records - i) * 1.5 for i in range(num_records)]
    f_a = np.random.normal(loc=10.0, scale=2.5, size=num_records).tolist()
    f_b = np.random.exponential(scale=5.0, size=num_records).tolist()
    f_c = np.random.uniform(low=0.0, high=100.0, size=num_records).tolist()
    f_d = np.random.standard_t(df=10, size=num_records).tolist()
    cats = np.random.choice(categories, size=num_records).tolist()
    labels = (np.array(f_a) + np.array(f_b) > 15.0).astype(int) + (np.array(f_c) > 50.0).astype(int)
    labels = np.clip(labels, 0, 3).tolist()

    df = pl.DataFrame(
        {
            "id": ids,
            "timestamp_epoch": timestamps,
            "feature_a": f_a,
            "feature_b": f_b,
            "feature_c": f_c,
            "feature_d": f_d,
            "category": cats,
            "target_class": labels,
        }
    )
    return df


def validate_and_filter_raw(raw_df: pl.DataFrame, min_rows: int = 10) -> pl.DataFrame:
    """
    Validates the ingested raw data against the formal DatasetContract.
    """
    contract = DatasetContract(
        dataset_name="raw_telemetry",
        expected_columns=(
            "id",
            "timestamp_epoch",
            "feature_a",
            "feature_b",
            "feature_c",
            "feature_d",
            "category",
            "target_class",
        ),
        min_rows=min_rows,
        max_null_ratio=0.01,
        description="Ingested raw telemetry events",
    )

    outcome = DataContractValidator.validate_polars(raw_df, contract)
    if not outcome.admitted:
        raise ValueError(
            f"Dataset failed admission! Disposition: {outcome.disposition}, Violations: {outcome.violations}"
        )

    # Polars transformations: deduplicate and sort by timestamp
    cleaned_df = raw_df.lazy().unique(subset=["id"]).sort("timestamp_epoch").collect()
    return cleaned_df
