"""
Unit tests for Kedro ModelArtifactDataset.
"""

from pathlib import Path

import pytest
import torch
from kedro.io.core import DatasetError

from ckodex_aiops.datasets.model_dataset import ModelArtifactDataSet, ModelArtifactDataset
from ckodex_aiops.models.network import VectorRepresentationNet


def test_model_artifact_dataset_save_load(tmp_path: Path):
    weights_file = tmp_path / "model.safetensors"
    dataset = ModelArtifactDataset(filepath=str(weights_file))

    model = VectorRepresentationNet(input_dim=16, hidden_dim=32, num_classes=2)
    original_state = model.state_dict()
    metadata = {
        "model_architecture": "VectorRepresentationNet",
        "input_dim": 16,
        "hidden_dim": 32,
        "num_classes": 2,
        "version": "1.0.0",
    }

    payload = {
        "state_dict": original_state,
        "metadata": metadata,
    }

    # Save
    dataset.save(payload)
    assert weights_file.exists()
    assert (tmp_path / "model_metadata.json").exists()

    # Load
    loaded = dataset.load()
    assert "state_dict" in loaded
    assert "metadata" in loaded
    assert loaded["metadata"]["version"] == "1.0.0"
    assert loaded["metadata"]["input_dim"] == 16

    # Verify tensor shapes match
    for key, tensor in original_state.items():
        assert key in loaded["state_dict"]
        assert loaded["state_dict"][key].shape == tensor.shape
        assert torch.allclose(loaded["state_dict"][key], tensor)


def test_model_artifact_dataset_directory_path(tmp_path: Path):
    model_dir = tmp_path / "models"
    dataset = ModelArtifactDataSet(filepath=str(model_dir))

    model = VectorRepresentationNet(input_dim=8, hidden_dim=16, num_classes=2)
    payload = {
        "state_dict": model.state_dict(),
        "metadata": {"input_dim": 8, "hidden_dim": 16, "num_classes": 2},
    }

    dataset.save(payload)
    assert (model_dir / "model.safetensors").exists()
    assert (model_dir / "model_metadata.json").exists()

    loaded = dataset.load()
    assert loaded["metadata"]["input_dim"] == 8


def test_model_artifact_dataset_not_found(tmp_path: Path):
    non_existent = tmp_path / "missing.safetensors"
    dataset = ModelArtifactDataset(filepath=str(non_existent))

    with pytest.raises(DatasetError, match="Model weights file not found"):
        dataset.load()


def test_model_artifact_dataset_invalid_save(tmp_path: Path):
    dataset = ModelArtifactDataset(filepath=str(tmp_path / "model.safetensors"))
    with pytest.raises(DatasetError, match="Expected dict with 'state_dict' key"):
        dataset.save("invalid_payload")  # type: ignore[arg-type]
