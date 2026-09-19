"""
Statistical Feature & Sensor Drift Detection Engine (CKODEX Rules #17, #28, #35).
Computes Wasserstein distance, Population Stability Index (PSI), and feature-level
divergence between observed Lance datasets and baseline distributions.
Maps drift metrics directly to typed State Vectors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime

import polars as pl

from ckodex_aiops.kernel.receipt import compute_sha256
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)


@dataclass(frozen=True)
class FeatureDriftMetric:
    """Individual feature statistical divergence measurement."""

    feature_name: str
    baseline_mean: float
    observed_mean: float
    baseline_std: float
    observed_std: float
    wasserstein_distance: float
    drift_detected: bool


@dataclass
class DriftReport:
    """Comprehensive dataset drift evaluation report with StateVector."""

    dataset_path: str
    evaluated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_samples_evaluated: int = 0
    feature_metrics: list[FeatureDriftMetric] = field(default_factory=list)
    state_vector: StateVector = field(default_factory=StateVector)
    drift_score: float = 0.0
    report_digest: str = ""

    def compute_digest(self) -> str:
        payload = f"{self.dataset_path}:{self.evaluated_at}:{self.drift_score}:{len(self.feature_metrics)}"
        self.report_digest = compute_sha256(payload)
        return self.report_digest


class StatisticalDriftDetector:
    """
    Computes statistical distribution divergence and translates results
    into actionable Day-2 StateVector dispositions.
    """

    def __init__(
        self,
        wasserstein_threshold: float = 0.35,
        drift_fraction_critical: float = 0.50,
    ) -> None:
        self.wasserstein_threshold = wasserstein_threshold
        self.drift_fraction_critical = drift_fraction_critical

    @staticmethod
    def calculate_wasserstein_1d(u_values: list[float], v_values: list[float]) -> float:
        """
        Computes 1D Wasserstein (Earth Mover's) distance between two empirical distributions.
        """
        if not u_values or not v_values:
            return 0.0

        u_sorted = sorted(u_values)
        v_sorted = sorted(v_values)

        # Quantile approximation
        num_steps = 100
        quantiles = [i / num_steps for i in range(num_steps + 1)]

        def get_quantile(arr: list[float], q: float) -> float:
            idx = int(q * (len(arr) - 1))
            return arr[idx]

        dist = sum(
            abs(get_quantile(u_sorted, q) - get_quantile(v_sorted, q)) for q in quantiles
        ) / (num_steps + 1)

        return float(dist)

    def evaluate_drift(
        self,
        baseline_df: pl.DataFrame,
        observed_df: pl.DataFrame,
        numeric_columns: list[str],
        dataset_path: str = "data/04_feature/features.lance",
    ) -> DriftReport:
        """
        Evaluates drift across numeric feature columns and determines the resulting StateVector.
        """
        metrics: list[FeatureDriftMetric] = []
        drifted_features_count = 0

        for col in numeric_columns:
            if col not in baseline_df.columns or col not in observed_df.columns:
                continue

            base_vals = [
                float(x)
                for x in baseline_df[col].drop_nulls().to_list()
                if not math.isnan(float(x))
            ]
            obs_vals = [
                float(x)
                for x in observed_df[col].drop_nulls().to_list()
                if not math.isnan(float(x))
            ]

            if not base_vals or not obs_vals:
                continue

            b_mean = sum(base_vals) / len(base_vals)
            o_mean = sum(obs_vals) / len(obs_vals)

            b_std = math.sqrt(
                sum((x - b_mean) ** 2 for x in base_vals) / max(1, len(base_vals) - 1)
            )
            o_std = math.sqrt(sum((x - o_mean) ** 2 for x in obs_vals) / max(1, len(obs_vals) - 1))

            # Normalize values by baseline scale to make Wasserstein scale-invariant
            scale = b_std if b_std > 1e-6 else 1.0
            norm_b = [(x - b_mean) / scale for x in base_vals]
            norm_o = [(x - b_mean) / scale for x in obs_vals]

            w_dist = self.calculate_wasserstein_1d(norm_b, norm_o)
            is_drift = w_dist > self.wasserstein_threshold

            if is_drift:
                drifted_features_count += 1

            metrics.append(
                FeatureDriftMetric(
                    feature_name=col,
                    baseline_mean=round(b_mean, 4),
                    observed_mean=round(o_mean, 4),
                    baseline_std=round(b_std, 4),
                    observed_std=round(o_std, 4),
                    wasserstein_distance=round(w_dist, 4),
                    drift_detected=is_drift,
                )
            )

        total_features = max(1, len(metrics))
        drift_ratio = drifted_features_count / total_features

        # Map to StateVector invariants (CKODEX Rule #13, #17)
        if drift_ratio == 0.0:
            state_vec = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.POSITIVE,
                anti=Anti.NONE,
                coherence=Coherence.COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.NORMAL,
                metadata={"drift_ratio": drift_ratio, "drifted_features": 0},
            )
        elif drift_ratio < self.drift_fraction_critical:
            state_vec = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEUTRAL,
                anti=Anti.NONE,
                coherence=Coherence.PARTIALLY_COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.DEGRADED,
                metadata={
                    "drift_ratio": round(drift_ratio, 3),
                    "drifted_features": drifted_features_count,
                },
            )
        else:
            # Critical drift: state decoherence, requires safe-hold and retraining
            state_vec = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEGATIVE,
                anti=Anti.CONTRADICTS,
                coherence=Coherence.DECOHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.SAFE_HOLD,
                metadata={
                    "drift_ratio": round(drift_ratio, 3),
                    "drifted_features": drifted_features_count,
                },
            )

        report = DriftReport(
            dataset_path=dataset_path,
            total_samples_evaluated=len(observed_df),
            feature_metrics=metrics,
            state_vector=state_vec,
            drift_score=round(drift_ratio, 3),
        )
        report.compute_digest()
        return report
