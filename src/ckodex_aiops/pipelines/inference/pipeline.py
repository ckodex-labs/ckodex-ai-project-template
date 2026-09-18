"""
Distributed Inference Kedro Pipeline.
"""

from kedro.pipeline import Pipeline, node

from ckodex_aiops.pipelines.inference.nodes import run_distributed_inference


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=run_distributed_inference,
                inputs=[
                    "model_artifact",
                    "features_lance",
                    "params:inference.num_ray_actors",
                    "params:inference.batch_size",
                ],
                outputs="predictions_lance",
                name="run_distributed_inference_node",
            ),
        ]
    )
