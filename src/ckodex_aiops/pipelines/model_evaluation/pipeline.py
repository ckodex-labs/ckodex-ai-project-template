"""
Model Evaluation Kedro Pipeline.
"""

from kedro.pipeline import Pipeline, node

from ckodex_aiops.pipelines.model_evaluation.nodes import evaluate_model_conformance


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=evaluate_model_conformance,
                inputs=[
                    "model_artifact",
                    "features_lance",
                    "params:model_evaluation.min_accuracy_threshold",
                ],
                outputs="evaluation_report",
                name="evaluate_model_conformance_node",
            ),
        ]
    )
