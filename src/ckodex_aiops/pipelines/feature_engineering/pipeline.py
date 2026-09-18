"""
Feature Engineering Kedro Pipeline.
"""

from kedro.pipeline import Pipeline, node

from ckodex_aiops.pipelines.feature_engineering.nodes import (
    compute_polars_features,
    generate_distributed_embeddings,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=compute_polars_features,
                inputs="admitted_telemetry_lance",
                outputs="normalized_telemetry_df",
                name="compute_polars_features_node",
            ),
            node(
                func=generate_distributed_embeddings,
                inputs=[
                    "normalized_telemetry_df",
                    "params:feature_engineering.embedding_dim",
                    "params:feature_engineering.num_ray_actors",
                    "params:feature_engineering.batch_size",
                ],
                outputs="features_lance",
                name="generate_distributed_embeddings_node",
            ),
        ]
    )
