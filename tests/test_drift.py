"""Tests for Statistical Feature & Sensor Drift Detection Engine.
Validates Wasserstein distance calculations and StateVector mappings.
"""

from __future__ import annotations

import polars as pl

from ckodex_aiops.kernel.drift import StatisticalDriftDetector
from ckodex_aiops.kernel.state_vector import OperationalLifecycle


def test_wasserstein_calculation_identical():
    """Identical distributions must have zero Wasserstein distance."""
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    dist = StatisticalDriftDetector.calculate_wasserstein_1d(vals, vals)
    assert dist == 0.0


def test_drift_detection_clean():
    """Undrifted datasets must return NORMAL lifecycle and zero drift score."""
    base_df = pl.DataFrame(
        {
            "feat_a": [1.0, 2.0, 3.0, 4.0, 5.0] * 10,
            "feat_b": [10.0, 20.0, 30.0, 40.0, 50.0] * 10,
        }
    )
    obs_df = pl.DataFrame(
        {
            "feat_a": [1.1, 2.05, 2.95, 4.02, 5.01] * 10,
            "feat_b": [10.1, 19.9, 30.2, 39.8, 50.1] * 10,
        }
    )

    detector = StatisticalDriftDetector(wasserstein_threshold=0.35)
    report = detector.evaluate_drift(base_df, obs_df, numeric_columns=["feat_a", "feat_b"])

    assert report.drift_score == 0.0
    assert report.state_vector.lifecycle == OperationalLifecycle.NORMAL
    assert len(report.feature_metrics) == 2


def test_drift_detection_critical_shift():
    """Substantial distribution shift must trigger SAFE_HOLD lifecycle."""
    base_df = pl.DataFrame(
        {
            "feat_a": [1.0, 2.0, 3.0, 4.0, 5.0] * 10,
        }
    )
    # Shift mean by 50 standard deviations
    obs_df = pl.DataFrame(
        {
            "feat_a": [100.0, 120.0, 130.0, 140.0, 150.0] * 10,
        }
    )

    detector = StatisticalDriftDetector(wasserstein_threshold=0.35)
    report = detector.evaluate_drift(base_df, obs_df, numeric_columns=["feat_a"])

    assert report.drift_score == 1.0
    assert report.state_vector.lifecycle == OperationalLifecycle.SAFE_HOLD
    assert report.feature_metrics[0].drift_detected is True
