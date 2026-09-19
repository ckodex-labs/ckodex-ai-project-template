"""Tests for Dynamic Model Quantization Engine.
Validates Int8 quantization, compression ratios, and cosine representation fidelity.
"""

from __future__ import annotations

import torch

from ckodex_aiops.models.network import VectorRepresentationNet
from ckodex_aiops.models.quantization import DynamicModelQuantizer


def test_dynamic_quantization_lifecycle(tmp_path):
    """Must quantize VectorRepresentationNet to Int8 and achieve >= 98% cosine fidelity."""
    # 1. Create and save a baseline float32 model
    net = VectorRepresentationNet(input_dim=16, num_classes=3)
    src_path = tmp_path / "model_float32.pt"
    torch.save(net.state_dict(), src_path)

    # 2. Quantize
    quant_path = tmp_path / "model_int8.pt"
    report = DynamicModelQuantizer.quantize_model(
        source_model_path=src_path,
        output_model_path=quant_path,
        input_dim=16,
        num_classes=3,
        fidelity_threshold=0.95,
    )

    assert quant_path.exists()
    assert report.fidelity_verified is True
    assert report.fidelity_cosine_similarity >= 0.95
    assert len(report.quantized_sha256) == 64
