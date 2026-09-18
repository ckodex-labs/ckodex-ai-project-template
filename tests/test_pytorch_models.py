"""
Unit tests for PyTorch Models & Training.
"""

import numpy as np
import polars as pl
import torch

from ckodex_aiops.models.dataset import PolarsTorchDataset
from ckodex_aiops.models.network import VectorRepresentationNet
from ckodex_aiops.models.trainer import ModelTrainer


def test_vector_representation_net():
    model = VectorRepresentationNet(input_dim=16, hidden_dim=32, num_classes=3)
    x = torch.randn(4, 16)
    logits = model(x)
    assert logits.shape == (4, 3)

    features = model.extract_features(x)
    assert features.shape == (4, 32)
    assert model.count_parameters() > 0


def test_polars_torch_dataset():
    df = pl.DataFrame(
        {
            "vector": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            "target_class": [0, 1],
        }
    )
    dataset = PolarsTorchDataset(df, feature_col="vector", label_col="target_class")
    assert len(dataset) == 2
    feat, label = dataset[0]
    assert feat.shape == (3,)
    assert label.item() == 0


def test_model_trainer_and_checkpoint(temp_workspace):
    df = pl.DataFrame(
        {
            "vector": [np.random.randn(8).tolist() for _ in range(50)],
            "target_class": [i % 2 for i in range(50)],
        }
    )
    dataset = PolarsTorchDataset(df, feature_col="vector", label_col="target_class")
    model = VectorRepresentationNet(input_dim=8, hidden_dim=16, num_classes=2)

    trainer = ModelTrainer(model=model, learning_rate=0.01, device="cpu")
    fit_res = trainer.fit(train_dataset=dataset, epochs=2, batch_size=16)

    assert "history" in fit_res
    assert len(fit_res["history"]) == 2

    ckpt_path = temp_workspace / "model.pt"
    sha = trainer.save_checkpoint(ckpt_path)
    assert ckpt_path.exists()
    assert len(sha) == 64
