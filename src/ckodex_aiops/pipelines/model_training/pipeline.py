"""
Model Training Kedro Pipeline.
"""

from kedro.pipeline import Pipeline, node

from ckodex_aiops.pipelines.model_training.nodes import train_representation_model


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=train_representation_model,
                inputs=[
                    "features_lance",
                    "params:model.input_dim",
                    "params:model.hidden_dim",
                    "params:model.num_classes",
                    "params:model_training.epochs",
                    "params:model_training.batch_size",
                    "params:model_training.learning_rate",
                    "params:model.checkpoint_dir",
                ],
                outputs=["model_artifact", "training_history"],
                name="train_representation_model_node",
            ),
        ]
    )
