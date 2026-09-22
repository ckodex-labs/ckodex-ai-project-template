"""
Project Pipeline Registry.
Registers all Kedro pipelines for modular or end-to-end execution.
"""

from __future__ import annotations

from kedro.pipeline import Pipeline

from ckodex_aiops.pipelines import (
    data_ingestion,
    feature_engineering,
    inference,
    model_evaluation,
    model_training,
    physical_ai,
)


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines."""
    data_ingestion_pipeline = data_ingestion.create_pipeline()
    feature_engineering_pipeline = feature_engineering.create_pipeline()
    model_training_pipeline = model_training.create_pipeline()
    model_evaluation_pipeline = model_evaluation.create_pipeline()
    inference_pipeline = inference.create_pipeline()
    physical_ai_pipeline = physical_ai.create_pipeline()

    data_processing_pipeline = data_ingestion_pipeline + feature_engineering_pipeline
    training_and_eval_pipeline = model_training_pipeline + model_evaluation_pipeline

    full_pipeline = data_processing_pipeline + training_and_eval_pipeline + inference_pipeline

    return {
        "__default__": full_pipeline,
        "data_ingestion": data_ingestion_pipeline,
        "feature_engineering": feature_engineering_pipeline,
        "data_processing": data_processing_pipeline,
        "training": model_training_pipeline,
        "model_training": model_training_pipeline,
        "evaluation": model_evaluation_pipeline,
        "model_evaluation": model_evaluation_pipeline,
        "train_and_eval": training_and_eval_pipeline,
        "inference": inference_pipeline,
        "physical_ai": physical_ai_pipeline,
    }
