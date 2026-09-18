"""
Model Evaluation Pipeline Nodes.
Evaluates model performance and emits Conformance State Vector.
"""

from __future__ import annotations

from typing import Any

import polars as pl
from rich.console import Console
from torch.utils.data import DataLoader

from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)
from ckodex_aiops.models.dataset import PolarsTorchDataset
from ckodex_aiops.models.network import VectorRepresentationNet
from ckodex_aiops.models.trainer import ModelTrainer

console = Console()


def evaluate_model_conformance(
    model_artifact: dict[str, Any],
    features_df: pl.DataFrame,
    min_accuracy_threshold: float = 0.50,
) -> dict[str, Any]:
    """
    Evaluates PyTorch model against validation data and constructs conformance state vector.
    """
    metadata = model_artifact["metadata"]
    state_dict = model_artifact["state_dict"]

    model = VectorRepresentationNet(
        input_dim=metadata["input_dim"],
        hidden_dim=metadata["hidden_dim"],
        num_classes=metadata["num_classes"],
    )
    model.load_state_dict(state_dict)

    dataset = PolarsTorchDataset(features_df, feature_col="vector", label_col="target_class")
    loader = DataLoader(dataset, batch_size=64, shuffle=False)

    trainer = ModelTrainer(model=model)
    eval_metrics = trainer.evaluate(loader)

    accuracy = eval_metrics["accuracy"]
    loss = eval_metrics["loss"]

    # Conformance evaluation
    conformance_passed = accuracy >= min_accuracy_threshold
    state_vector = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE if conformance_passed else Valence.NEGATIVE,
        anti=Anti.NONE if conformance_passed else Anti.INVALIDATES,
        coherence=Coherence.COHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL
        if conformance_passed
        else OperationalLifecycle.DEGRADED,
        metadata={
            "accuracy": accuracy,
            "loss": loss,
            "min_threshold": min_accuracy_threshold,
            "throughput_rps": eval_metrics["throughput_samples_per_sec"],
            "model_digest": metadata.get("weights_sha256"),
        },
    )

    console.print(
        f"[bold {'green' if conformance_passed else 'red'}]Model Evaluation Conformance:[/bold {'green' if conformance_passed else 'red'}] "
        f"Accuracy: {accuracy:.2%} | Loss: {loss:.4f} | State: {state_vector.lifecycle.value}"
    )

    return {
        "metrics": eval_metrics,
        "conformance_passed": conformance_passed,
        "state_vector": {
            "presence": state_vector.presence.value,
            "valence": state_vector.valence.value,
            "anti": state_vector.anti.value,
            "coherence": state_vector.coherence.value,
            "evidence": state_vector.evidence.value,
            "lifecycle": state_vector.lifecycle.value,
            "metadata": state_vector.metadata,
        },
    }
