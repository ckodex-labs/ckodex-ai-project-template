"""
Model Training Pipeline Nodes.
Trains PyTorch VectorRepresentationNet model on Lance feature embeddings with hardware acceleration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl
from rich.console import Console

from ckodex_aiops.models.dataset import PolarsTorchDataset
from ckodex_aiops.models.network import VectorRepresentationNet
from ckodex_aiops.models.trainer import ModelTrainer

console = Console()


def train_representation_model(
    features_df: pl.DataFrame,
    input_dim: int = 32,
    hidden_dim: int = 64,
    num_classes: int = 4,
    epochs: int = 5,
    batch_size: int = 32,
    learning_rate: float = 1e-3,
    checkpoint_dir: str = "data/06_models",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Trains PyTorch model on feature vectors and persists weights with cryptographic verification.
    """
    # 80/20 train/val split using Polars
    total_rows = features_df.height
    train_size = int(total_rows * 0.8)
    shuffled_df = features_df.sample(fraction=1.0, shuffle=True, seed=42)

    train_df = shuffled_df.slice(0, train_size)
    val_df = shuffled_df.slice(train_size, total_rows - train_size)

    train_dataset = PolarsTorchDataset(train_df, feature_col="vector", label_col="target_class")
    val_dataset = PolarsTorchDataset(val_df, feature_col="vector", label_col="target_class")

    model = VectorRepresentationNet(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        num_classes=num_classes,
    )

    console.print(
        f"[bold cyan]PyTorch Network instantiated:[/bold cyan] {model.count_parameters()} trainable parameters."
    )

    trainer = ModelTrainer(model=model, learning_rate=learning_rate)
    training_results = trainer.fit(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        epochs=epochs,
        batch_size=batch_size,
    )

    # Persist memory-safe Safetensors checkpoint and legacy PT
    safetensors_path = Path(checkpoint_dir) / "model.safetensors"
    pt_path = Path(checkpoint_dir) / "model.pt"

    safetensors_sha256 = trainer.save_checkpoint(safetensors_path, format="safetensors")
    trainer.save_checkpoint(pt_path, format="pt")

    metadata = {
        "model_architecture": "VectorRepresentationNet",
        "input_dim": input_dim,
        "hidden_dim": hidden_dim,
        "num_classes": num_classes,
        "weights_sha256": safetensors_sha256,
        "checkpoint_path": str(safetensors_path),
        "safetensors_path": str(safetensors_path),
        "pt_path": str(pt_path),
        "device": training_results.get("device"),
        "epochs": epochs,
    }

    metadata_path = Path(checkpoint_dir) / "model_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    console.print(
        f"[bold green]✔ Training Complete:[/bold green] Checkpoints saved at {safetensors_path} and {pt_path} [dim](SHA256: {safetensors_sha256[:16]}...)[/dim]"
    )

    # Return model state dict in-memory along with metadata and history
    model_artifact = {
        "state_dict": model.state_dict(),
        "metadata": metadata,
    }

    return model_artifact, training_results
