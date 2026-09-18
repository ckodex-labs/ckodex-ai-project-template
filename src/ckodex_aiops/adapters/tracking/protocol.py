"""
Experiment Tracking & Observability Protocol (Rule #12 & Rule #38).
Defines the machine interface for logging the 4 truth channels:
1. Telemetry trace (hardware, durations, throughput)
2. Execution trace (nodes, runs, steps)
3. Decision trace (policy snapshots, state vectors)
4. Evidence trace (lineage receipts, cryptographic digests, safetensors artifacts)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from ckodex_aiops.kernel.receipt import LineageReceipt
from ckodex_aiops.kernel.state_vector import StateVector


class ExperimentTracker(Protocol):
    """
    Protocol for high-assurance experiment tracking and deep observability.
    """

    def start_run(self, run_name: str, tags: dict[str, str] | None = None) -> str:
        """Start a new experiment tracking run."""
        ...

    def log_params(self, params: dict[str, Any]) -> None:
        """Log hyperparameter configuration."""
        ...

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log performance and operational metrics."""
        ...

    def log_state_vector(self, vector: StateVector, step: int | None = None) -> None:
        """Log CKODEX StateVector product type S(e,t)."""
        ...

    def log_artifact(self, local_path: str | Path, artifact_type: str = "model") -> str:
        """Log artifact file (e.g. safetensors checkpoint) and return tracking URI."""
        ...

    def log_receipt(self, receipt: LineageReceipt) -> None:
        """Log cryptographic lineage receipt for evidence trail."""
        ...

    def end_run(self, status: str = "FINISHED") -> None:
        """Complete the active experiment run."""
        ...
