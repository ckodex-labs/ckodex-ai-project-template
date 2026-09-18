"""
Ray Actor & Co-Actor Parallelism Pattern (CKODEX Rule #31 & #38).
Implements asynchronous non-blocking telemetry and memory tracking co-actors
that run concurrently alongside compute-heavy InferenceActors.
"""

from __future__ import annotations

import collections
import time
from typing import Any

import ray


@ray.remote
class TelemetryCoactor:
    """
    Stateful co-actor that collects, aggregates, and flushes runtime telemetry
    asynchronously without blocking the primary compute actor's execution thread.
    """

    def __init__(self, buffer_size: int = 1000) -> None:
        self.buffer_size = buffer_size
        self.events: collections.deque[dict[str, Any]] = collections.deque(maxlen=buffer_size)
        self.total_recorded: int = 0
        self.created_at: float = time.time()

    def record_metric(
        self,
        actor_id: str,
        operation: str,
        duration_ms: float,
        sample_count: int,
        device: str,
    ) -> None:
        """Non-blocking telemetry ingest."""
        event = {
            "timestamp": time.time(),
            "actor_id": actor_id,
            "operation": operation,
            "duration_ms": duration_ms,
            "sample_count": sample_count,
            "device": device,
        }
        self.events.append(event)
        self.total_recorded += 1

    def flush_metrics(self) -> list[dict[str, Any]]:
        """Extract and clear buffered metrics."""
        flushed = list(self.events)
        self.events.clear()
        return flushed

    def get_summary(self) -> dict[str, Any]:
        """Returns aggregate telemetry metrics."""
        durations = [e["duration_ms"] for e in self.events]
        samples = sum(e["sample_count"] for e in self.events)
        avg_dur = sum(durations) / max(len(durations), 1)

        return {
            "buffered_events": len(self.events),
            "total_recorded_lifetime": self.total_recorded,
            "avg_duration_ms": round(avg_dur, 2),
            "total_samples_processed": samples,
            "uptime_sec": round(time.time() - self.created_at, 1),
        }
