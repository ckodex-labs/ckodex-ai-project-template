"""
Stateful Ray Actor: PyTorch Model Serving.
Maintains PyTorch model weights on target accelerator (MPS/CUDA/CPU) with dynamic batching.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import torch

import ray
from ckodex_aiops.models.network import VectorRepresentationNet


def resolve_accelerator_device(requested: str = "auto") -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if hasattr(torch, "mps") and torch.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


@ray.remote
class InferenceActor:
    """
    Ray Actor for stateful, low-latency PyTorch model inference.
    """

    def __init__(
        self,
        model_state_dict: dict[str, Any] | None = None,
        checkpoint_path: str | Path | None = None,
        input_dim: int = 32,
        hidden_dim: int = 64,
        num_classes: int = 4,
        device: str = "auto",
    ) -> None:
        self.actor_id = ray.get_runtime_context().get_actor_id()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.device = resolve_accelerator_device(device)

        # Instantiate model architecture
        self.model = VectorRepresentationNet(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            num_classes=num_classes,
        ).to(self.device)

        if checkpoint_path is not None:
            p = Path(checkpoint_path)
            if p.suffix == ".safetensors":
                import safetensors.torch

                # Safetensors mmap loading directly onto Apple Silicon Metal / CUDA
                state_dict = safetensors.torch.load_file(str(p), device=str(self.device))
                self.model.load_state_dict(state_dict)
            else:
                self.model.load_state_dict(torch.load(str(p), map_location=self.device))
        elif model_state_dict is not None:
            self.model.load_state_dict(model_state_dict)

        self.model.eval()

        self.total_inferences = 0
        self.total_errors = 0
        self.total_latency_ms = 0.0
        self.created_at = time.time()

        # Warm up
        self._warmup()

    def _warmup(self) -> None:
        dummy = torch.randn(2, self.input_dim, device=self.device)
        with torch.no_grad():
            self.model(dummy)

    def predict_batch(self, features: list[list[float]]) -> dict[str, Any]:
        """
        Execute forward pass for a batch of features.
        """
        start = time.perf_counter()
        try:
            tensor_in = torch.tensor(features, dtype=torch.float32, device=self.device)
            with torch.no_grad():
                logits = self.model(tensor_in)
                probs = torch.softmax(logits, dim=-1)
                preds = torch.argmax(probs, dim=-1)

            latency_ms = (time.perf_counter() - start) * 1000.0
            self.total_inferences += len(features)
            self.total_latency_ms += latency_ms

            return {
                "predictions": preds.cpu().tolist(),
                "probabilities": probs.cpu().tolist(),
                "latency_ms": latency_ms,
                "worker_id": str(self.actor_id),
                "device": str(self.device),
            }
        except Exception as e:
            self.total_errors += 1
            raise RuntimeError(f"Inference actor execution failure: {e}") from e

    def health_check(self) -> dict[str, Any]:
        return {
            "actor_id": str(self.actor_id),
            "status": "HEALTHY" if self.total_errors == 0 else "DEGRADED",
            "device": str(self.device),
            "total_inferences": self.total_inferences,
            "total_errors": self.total_errors,
            "avg_latency_ms": (round(self.total_latency_ms / max(self.total_inferences, 1), 3)),
            "uptime_seconds": round(time.time() - self.created_at, 1),
        }
