"""
Integration tests for Kedro Pipelines end-to-end.
"""

from ckodex_aiops.pipeline_registry import register_pipelines
from ckodex_aiops.pipelines.data_ingestion.nodes import (
    generate_synthetic_telemetry,
    validate_and_filter_raw,
)
from ckodex_aiops.pipelines.feature_engineering.nodes import (
    compute_polars_features,
    generate_distributed_embeddings,
)
from ckodex_aiops.pipelines.inference.nodes import run_distributed_inference
from ckodex_aiops.pipelines.model_evaluation.nodes import evaluate_model_conformance
from ckodex_aiops.pipelines.model_training.nodes import train_representation_model


def test_pipeline_registry():
    registry = register_pipelines()
    assert "__default__" in registry
    assert "data_ingestion" in registry
    assert "feature_engineering" in registry
    assert "training" in registry
    assert "evaluation" in registry
    assert "inference" in registry


def test_pipeline_nodes_end_to_end(temp_workspace):
    # 1. Ingestion
    raw = generate_synthetic_telemetry(num_records=80)
    admitted = validate_and_filter_raw(raw, min_rows=10)
    assert admitted.height == 80

    # 2. Features
    normed = compute_polars_features(admitted)
    features = generate_distributed_embeddings(
        normed, embedding_dim=16, num_actors=1, batch_size=40
    )
    assert "vector" in features.columns
    assert features.height == 80

    # 3. Training
    model_art, hist = train_representation_model(
        features,
        input_dim=16,
        hidden_dim=32,
        num_classes=4,
        epochs=2,
        batch_size=16,
        checkpoint_dir=str(temp_workspace / "models"),
    )
    assert "state_dict" in model_art

    # 4. Evaluation
    eval_report = evaluate_model_conformance(model_art, features, min_accuracy_threshold=0.1)
    assert "metrics" in eval_report
    assert "state_vector" in eval_report

    # 5. Inference
    preds = run_distributed_inference(model_art, features, num_actors=1, batch_size=40)
    assert "predicted_class" in preds.columns
    assert preds.height == 80
