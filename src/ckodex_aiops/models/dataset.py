"""
PyTorch Datasets backed by Lance and Polars.
Enables high-performance streaming directly into tensors without pandas overhead.
"""

from __future__ import annotations

from pathlib import Path

import lance
import numpy as np
import polars as pl
import torch
from torch.utils.data import Dataset


class PolarsTorchDataset(Dataset):
    """
    PyTorch Dataset directly backed by Polars DataFrame.
    """

    def __init__(
        self,
        df: pl.DataFrame,
        feature_col: str = "vector",
        label_col: str = "target_class",
    ) -> None:
        self.feature_col = feature_col
        self.label_col = label_col
        self.length = df.height

        # Fast numpy conversion
        vec_list = df[feature_col].to_list()
        self.features = torch.tensor(np.array(vec_list), dtype=torch.float32)

        self.labels: torch.Tensor | None
        if label_col in df.columns:
            labels = df[label_col].to_numpy()
            self.labels = torch.tensor(labels, dtype=torch.long)
        else:
            self.labels = None

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor | None]:
        feat = self.features[idx]
        label = self.labels[idx] if self.labels is not None else None
        return feat, label


class LanceTorchDataset(Dataset):
    """
    PyTorch Dataset reading directly from a Lance table.
    Supports index-based random access via Lance batches.
    """

    def __init__(
        self,
        lance_path: str | Path,
        feature_col: str = "vector",
        label_col: str = "target_class",
        batch_size: int = 256,
    ) -> None:
        self.lance_path = Path(lance_path)
        self.feature_col = feature_col
        self.label_col = label_col
        self.batch_size = batch_size

        self.ds = lance.dataset(str(self.lance_path))
        self.total_rows = self.ds.count_rows()

        # Cache in memory for dataset if small enough, or stream
        scanner = self.ds.scanner(columns=[feature_col, label_col])
        tbl = scanner.to_table()
        vec_data = np.stack(tbl[feature_col].to_numpy())
        self.features = torch.from_numpy(vec_data).float()
        self.labels = torch.from_numpy(tbl[label_col].to_numpy()).long()

    def __len__(self) -> int:
        return self.total_rows

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.labels[idx]
