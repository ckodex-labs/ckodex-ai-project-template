"""
Physical AI Kedro Pipeline.
"""

from kedro.pipeline import Pipeline, node

from ckodex_aiops.pipelines.physical_ai.nodes import (
    extract_kinematic_features_and_events,
    generate_multimodal_robotics_telemetry,
    ingest_physical_ai_dataset,
    mine_physical_ai_events,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=generate_multimodal_robotics_telemetry,
                inputs=[
                    "params:physical_ai.num_episodes",
                    "params:physical_ai.steps_per_episode",
                    "params:physical_ai.embedding_dim",
                ],
                outputs="raw_physical_telemetry_df",
                name="generate_physical_telemetry_node",
            ),
            node(
                func=extract_kinematic_features_and_events,
                inputs=[
                    "raw_physical_telemetry_df",
                    "params:physical_ai.rolling_window_size",
                ],
                outputs="processed_physical_telemetry_df",
                name="extract_kinematic_features_node",
            ),
            node(
                func=ingest_physical_ai_dataset,
                inputs=[
                    "processed_physical_telemetry_df",
                    "params:physical_ai.target_path",
                ],
                outputs="physical_ai_lance_path",
                name="ingest_physical_ai_lance_node",
            ),
            node(
                func=mine_physical_ai_events,
                inputs=[
                    "physical_ai_lance_path",
                    "params:physical_ai.mining_filter",
                    "params:physical_ai.mining_limit",
                ],
                outputs="physical_ai_mining_report",
                name="mine_physical_ai_events_node",
            ),
        ]
    )
