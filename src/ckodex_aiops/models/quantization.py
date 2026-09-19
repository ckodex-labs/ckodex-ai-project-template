"""
Hardware-Aware Dynamic Quantization Engine (CKODEX Rule #30 & #36).
Applies dynamic Int8 quantization to neural networks, verifies representation fidelity
via cosine similarity, and emits cryptographic quantization receipts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F

from ckodex_aiops.kernel.receipt import hash_file
from ckodex_aiops.models.network import VectorRepresentationNet
from ckodex_aiops.models.trainer import load_checkpoint


@dataclass(frozen=True)
class QuantizationReport:
    """Verification receipt of model quantization."""

    original_path: str
    quantized_path: str
    original_size_bytes: int
    quantized_size_bytes: int
    compression_ratio: float
    fidelity_cosine_similarity: float
    quantization_duration_ms: float
    quantized_sha256: str
    fidelity_verified: bool


class DynamicModelQuantizer:
    """
    Performs dynamic Int8 post-training quantization on PyTorch models.
    """

    @classmethod
    def quantize_model(
        cls,
        source_model_path: str | Path,
        output_model_path: str | Path,
        input_dim: int = 16,
        num_classes: int = 3,
        fidelity_threshold: float = 0.98,
    ) -> QuantizationReport:
        src = Path(source_model_path)
        out = Path(output_model_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()

        # Configure supported quantized engine (qnnpack on ARM64 / macOS, fbgemm on x86)
        if "qnnpack" in torch.backends.quantized.supported_engines:
            torch.backends.quantized.engine = "qnnpack"
        elif "fbgemm" in torch.backends.quantized.supported_engines:
            torch.backends.quantized.engine = "fbgemm"

        # Auto-detect dimensions from checkpoint if present
        if src.exists():
            try:
                if src.suffix == ".safetensors":
                    import safetensors.torch

                    state = safetensors.torch.load_file(str(src), device="cpu")
                else:
                    state = torch.load(str(src), map_location="cpu", weights_only=True)
                if "input_proj.0.weight" in state:
                    input_dim = state["input_proj.0.weight"].shape[1]
                if "head.weight" in state:
                    num_classes = state["head.weight"].shape[0]
            except Exception:
                pass

        # Load float32 baseline model
        base_model = VectorRepresentationNet(input_dim=input_dim, num_classes=num_classes)
        if src.exists():
            load_checkpoint(base_model, src, device="cpu")
        base_model.eval()

        # Perform dynamic Int8 quantization on linear layers
        quantized_model = torch.ao.quantization.quantize_dynamic(
            base_model,
            {torch.nn.Linear},
            dtype=torch.qint8,
        )

        # Measure representation fidelity on synthetic test inputs
        test_inputs = torch.randn(64, input_dim)
        with torch.no_grad():
            base_logits = base_model(test_inputs)
            quant_logits = quantized_model(test_inputs)

            # Cosine similarity across batch
            cos_sim = F.cosine_similarity(base_logits, quant_logits, dim=-1).mean().item()

        # Save quantized model
        # PyTorch quantized modules save cleanly via torch.save
        torch.save(quantized_model.state_dict(), out)

        duration_ms = (time.perf_counter() - start) * 1000
        orig_size = src.stat().st_size if src.exists() else 0
        quant_size = out.stat().st_size
        comp_ratio = round(orig_size / max(1, quant_size), 2)
        quant_digest = hash_file(out)

        fidelity_ok = cos_sim >= fidelity_threshold

        return QuantizationReport(
            original_path=str(src),
            quantized_path=str(out),
            original_size_bytes=orig_size,
            quantized_size_bytes=quant_size,
            compression_ratio=comp_ratio,
            fidelity_cosine_similarity=round(cos_sim, 4),
            quantization_duration_ms=round(duration_ms, 2),
            quantized_sha256=quant_digest,
            fidelity_verified=fidelity_ok,
        )
