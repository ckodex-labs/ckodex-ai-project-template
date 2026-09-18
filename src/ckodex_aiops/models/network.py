"""
PyTorch Neural Network Architecture: VectorRepresentationNet.
Modern representation network with residual projections, layer normalization, and GELU activations.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    def __init__(self, hidden_dim: int, dropout_rate: float = 0.1) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )
        self.activation = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.activation(x + self.block(x))


class VectorRepresentationNet(nn.Module):
    """
    Representation learning network for high-dimensional vector embeddings and multi-class classification.
    """

    def __init__(
        self,
        input_dim: int = 32,
        hidden_dim: int = 64,
        num_classes: int = 4,
        num_layers: int = 2,
        dropout_rate: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes

        # Input projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
        )

        # Residual backbone
        self.backbone = nn.Sequential(
            *[ResidualBlock(hidden_dim, dropout_rate) for _ in range(num_layers)]
        )

        # Classifier head
        self.head = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        projected = self.input_proj(x)
        features = self.backbone(projected)
        logits = self.head(features)
        return logits

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract latent representation vector before final classifier."""
        projected = self.input_proj(x)
        return self.backbone(projected)

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
