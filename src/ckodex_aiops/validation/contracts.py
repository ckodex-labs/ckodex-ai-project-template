"""
Validation schemas and data contract definitions using Pydantic v2.
Shared validation layer accessible by transports, pipelines, and actors.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestionRecordSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique record identifier")
    timestamp_epoch: float = Field(..., description="Event timestamp in seconds since epoch")
    feature_a: float = Field(..., description="Numerical feature A")
    feature_b: float = Field(..., description="Numerical feature B")
    category: str = Field(..., description="Categorical feature value")
    target_class: int = Field(..., ge=0, le=9, description="Target classification label (0-9)")


class VectorSearchQuery(BaseModel):
    vector: list[float] = Field(..., min_length=1, description="Query vector embedding")
    limit: int = Field(default=10, ge=1, le=1000, description="Top K nearest neighbors")
    filter_expr: str | None = Field(default=None, description="Optional SQL filter expression")


class ValidationOutcome(BaseModel):
    admitted: bool
    disposition: str  # ADMIT, ADMIT_WITH_OBLIGATIONS, DENY, ESCALATE, SAFE_HOLD, QUARANTINE
    violations: list[str] = Field(default_factory=list)
    obligations: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
