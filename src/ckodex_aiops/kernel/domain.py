"""
Pure Semantic Kernel: Core AI Domain Contracts.
Governs data contracts, model artifact declarations, and inference envelopes.
Zero framework imports (no torch, ray, lance, or kedro here).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DatasetContract:
    dataset_name: str
    expected_columns: tuple[str, ...]
    vector_column: str | None = None
    vector_dimension: int | None = None
    min_rows: int = 1
    max_null_ratio: float = 0.05
    description: str = ""


@dataclass(frozen=True)
class ModelArtifactMetadata:
    model_name: str
    version: str
    architecture: str
    input_dimension: int
    output_dimension: int
    weights_digest: str
    hyperparameters: Mapping[str, Any] = field(default_factory=dict)
    trained_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class EvaluationMetrics:
    accuracy: float
    loss: float
    precision: float
    recall: float
    f1_score: float
    latency_p95_ms: float
    throughput_rps: float
    conformance_passed: bool
    details: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class InferenceRequest:
    request_id: str
    features: tuple[tuple[float, ...], ...]
    top_k: int = 5
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InferenceResponse:
    request_id: str
    predictions: tuple[int, ...]
    probabilities: tuple[tuple[float, ...], ...]
    latency_ms: float
    worker_id: str
