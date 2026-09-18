"""
Data Ingestion Kedro Pipeline.
"""

from kedro.pipeline import Pipeline, node

from ckodex_aiops.pipelines.data_ingestion.nodes import (
    generate_synthetic_telemetry,
    validate_and_filter_raw,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=generate_synthetic_telemetry,
                inputs="params:data_ingestion.num_records",
                outputs="raw_telemetry_df",
                name="generate_synthetic_telemetry_node",
            ),
            node(
                func=validate_and_filter_raw,
                inputs=["raw_telemetry_df", "params:data_ingestion.min_rows"],
                outputs="admitted_telemetry_lance",
                name="validate_and_filter_raw_node",
            ),
        ]
    )
