"""
Feature Engineering Pipeline Nodes.
Combines Polars vectorized transformations with Ray Actor pool distributed embedding generation.
"""

from __future__ import annotations

import polars as pl
from rich.console import Console

from ckodex_aiops.adapters.ray.actors.pool import ActorPoolManager
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager
from ckodex_aiops.kernel.domain import DatasetContract
from ckodex_aiops.validation.validators import DataContractValidator

console = Console()


def compute_polars_features(df: pl.DataFrame) -> pl.DataFrame:
    """
    Polars vectorized feature engineering with window expressions and normalizations.
    """
    transformed = (
        df.lazy()
        .with_columns(
            [
                (
                    (pl.col("feature_a") - pl.col("feature_a").mean())
                    / (pl.col("feature_a").std() + 1e-6)
                ).alias("norm_a"),
                (
                    (pl.col("feature_b") - pl.col("feature_b").mean())
                    / (pl.col("feature_b").std() + 1e-6)
                ).alias("norm_b"),
                (
                    (pl.col("feature_c") - pl.col("feature_c").mean())
                    / (pl.col("feature_c").std() + 1e-6)
                ).alias("norm_c"),
                (
                    (pl.col("feature_d") - pl.col("feature_d").mean())
                    / (pl.col("feature_d").std() + 1e-6)
                ).alias("norm_d"),
            ]
        )
        .collect()
    )
    return transformed


def generate_distributed_embeddings(
    df: pl.DataFrame,
    embedding_dim: int = 32,
    num_actors: int = 2,
    batch_size: int = 250,
) -> pl.DataFrame:
    """
    Distributes vector embedding projection across a stateful Ray Actor pool.
    """
    RayRuntimeManager.initialize()

    # Extract numerical matrices
    feature_matrix = df.select(["norm_a", "norm_b", "norm_c", "norm_d"]).to_numpy().tolist()
    total_samples = len(feature_matrix)

    # Chunk input for actor pool
    chunks = [feature_matrix[i : i + batch_size] for i in range(0, total_samples, batch_size)]

    console.print(
        f"[cyan]Dispatching {total_samples} samples in {len(chunks)} chunks across {num_actors} Ray Actors...[/cyan]"
    )
    pool = ActorPoolManager.create_embedding_pool(size=num_actors, embedding_dim=embedding_dim)

    try:
        results = pool.dispatch_batch("generate_embeddings", chunks)
        # Flatten results
        all_embeddings = [emb for chunk_result in results for emb in chunk_result]

        # Attach embedding vectors to Polars DataFrame
        features_df = df.with_columns(pl.Series("vector", all_embeddings))

        # Validate feature contract
        contract = DatasetContract(
            dataset_name="features_with_embeddings",
            expected_columns=(
                "id",
                "norm_a",
                "norm_b",
                "norm_c",
                "norm_d",
                "vector",
                "target_class",
            ),
            vector_column="vector",
            vector_dimension=embedding_dim,
            min_rows=1,
            max_null_ratio=0.0,
        )
        outcome = DataContractValidator.validate_polars(features_df, contract)
        if not outcome.admitted:
            raise ValueError(f"Feature dataset validation failed: {outcome.violations}")

        return features_df

    finally:
        pool.terminate()
