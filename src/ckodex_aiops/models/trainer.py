"""
PyTorch Accelerated Model Trainer.
Supports Apple Silicon MPS, NVIDIA CUDA, and CPU execution with cryptographic model checkpointing.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import safetensors.torch
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset

from ckodex_aiops.kernel.receipt import compute_sha256
from ckodex_aiops.models.network import VectorRepresentationNet


class ModelTrainer:
    """
    Production-grade PyTorch model training and validation runner.
    """

    def __init__(
        self,
        model: VectorRepresentationNet,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        device: str = "auto",
    ) -> None:
        self.model = model
        if device == "auto":
            if hasattr(torch, "mps") and torch.mps.is_available():
                self.device = torch.device("mps")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        self.model.to(self.device)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

    def train_epoch(self, dataloader: DataLoader) -> tuple[float, float]:
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for batch_x, batch_y in dataloader:
            if batch_y is None:
                continue
            batch_x = batch_x.to(self.device)
            batch_y = batch_y.to(self.device)

            self.optimizer.zero_grad()
            logits = self.model(batch_x)
            loss = self.criterion(logits, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            total_loss += loss.item() * len(batch_y)
            preds = torch.argmax(logits, dim=-1)
            correct += (preds == batch_y).sum().item()
            total += len(batch_y)

        avg_loss = total_loss / max(total, 1)
        accuracy = correct / max(total, 1)
        return avg_loss, accuracy

    def evaluate(self, dataloader: DataLoader) -> dict[str, float]:
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        start = time.perf_counter()

        with torch.no_grad():
            for batch_x, batch_y in dataloader:
                if batch_y is None:
                    continue
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                logits = self.model(batch_x)
                loss = self.criterion(logits, batch_y)

                total_loss += loss.item() * len(batch_y)
                preds = torch.argmax(logits, dim=-1)
                correct += (preds == batch_y).sum().item()
                total += len(batch_y)

        duration_sec = time.perf_counter() - start
        avg_loss = total_loss / max(total, 1)
        accuracy = correct / max(total, 1)
        throughput = total / max(duration_sec, 1e-6)

        return {
            "loss": float(avg_loss),
            "accuracy": float(accuracy),
            "total_evaluated": float(total),
            "duration_sec": float(duration_sec),
            "throughput_samples_per_sec": float(throughput),
        }

    def fit(
        self,
        train_dataset: Dataset,
        val_dataset: Dataset | None = None,
        epochs: int = 5,
        batch_size: int = 32,
    ) -> dict[str, Any]:
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        scheduler = CosineAnnealingLR(self.optimizer, T_max=epochs, eta_min=1e-5)

        history = []
        for epoch in range(1, epochs + 1):
            train_loss, train_acc = self.train_epoch(train_loader)
            scheduler.step()
            epoch_stats = {
                "epoch": epoch,
                "train_loss": train_loss,
                "train_acc": train_acc,
            }
            if val_dataset:
                val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
                val_metrics = self.evaluate(val_loader)
                epoch_stats["val_loss"] = val_metrics["loss"]
                epoch_stats["val_acc"] = val_metrics["accuracy"]

            history.append(epoch_stats)

        return {"history": history, "device": str(self.device)}

    def save_checkpoint(
        self,
        path: str | Path,
        format: str | None = None,
    ) -> str:
        """
        Saves model weights and returns SHA256 digest of checkpoint file.
        Supports format="safetensors" (zero-copy, mmap, memory-safe) or format="pt".
        """
        checkpoint_path = Path(path)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        is_safetensors = (
            (format == "safetensors")
            or (checkpoint_path.suffix == ".safetensors")
            or (format is None and checkpoint_path.suffix != ".pt")
        )

        if is_safetensors:
            if checkpoint_path.suffix != ".safetensors":
                checkpoint_path = checkpoint_path.with_suffix(".safetensors")
            # Convert tensors to CPU for saving if on MPS/CUDA
            state_dict = {k: v.contiguous().cpu() for k, v in self.model.state_dict().items()}
            safetensors.torch.save_file(state_dict, str(checkpoint_path))
        else:
            torch.save(self.model.state_dict(), str(checkpoint_path))

        return compute_sha256(checkpoint_path.read_bytes())
