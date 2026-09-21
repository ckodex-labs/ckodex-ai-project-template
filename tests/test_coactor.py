"""Tests for Ray Actor & Co-Actor Concurrency Pattern.
Validates TelemetryCoactor buffer limits, telemetry aggregation, and metric flushing.
"""

from __future__ import annotations

import pytest
import ray

from ckodex_aiops.adapters.ray.actors.coactor import TelemetryCoactor
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager


@pytest.fixture(scope="module")
def init_ray():
    """Initializes local Ray session safely via RayRuntimeManager."""
    RayRuntimeManager.initialize()
    yield


def test_telemetry_coactor_lifecycle(init_ray):
    """TelemetryCoactor must record metrics, aggregate summaries, and flush asynchronously."""
    from typing import Any

    coactor_cls: Any = TelemetryCoactor
    coactor = coactor_cls.remote(buffer_size=50)

    # Record multiple events
    ray.get(
        coactor.record_metric.remote(
            actor_id="worker-01",
            operation="forward_pass",
            duration_ms=12.5,
            sample_count=64,
            device="mps",
        )
    )
    ray.get(
        coactor.record_metric.remote(
            actor_id="worker-01",
            operation="forward_pass",
            duration_ms=15.5,
            sample_count=64,
            device="mps",
        )
    )

    summary = ray.get(coactor.get_summary.remote())
    assert summary["buffered_events"] == 2
    assert summary["total_recorded_lifetime"] == 2
    assert summary["total_samples_processed"] == 128
    assert summary["avg_duration_ms"] == 14.0

    # Flush metrics
    flushed = ray.get(coactor.flush_metrics.remote())
    assert len(flushed) == 2
    assert flushed[0]["operation"] == "forward_pass"
    assert flushed[0]["device"] == "mps"

    # Post-flush state
    empty_summary = ray.get(coactor.get_summary.remote())
    assert empty_summary["buffered_events"] == 0
    assert empty_summary["total_recorded_lifetime"] == 2

    ray.kill(coactor)
