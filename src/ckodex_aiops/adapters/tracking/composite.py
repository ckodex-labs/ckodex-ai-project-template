"""
Composite Experiment Tracker.
Fans out observability signals to both the local Air-Gap Flight Recorder and MLflow tracking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ckodex_aiops.adapters.tracking.flight_recorder import FlightRecorderTracker
from ckodex_aiops.adapters.tracking.mlflow_adapter import MLflowTracker
from ckodex_aiops.adapters.tracking.protocol import ExperimentTracker
from ckodex_aiops.adapters.tracking.research_evidence_adapter import ResearchEvidenceTracker
from ckodex_aiops.kernel.receipt import LineageReceipt
from ckodex_aiops.kernel.state_vector import StateVector


class CompositeTracker:
    """
    Broadcasts telemetry, execution traces, StateVectors, and artifacts to all registered trackers.
    """

    def __init__(self, trackers: list[ExperimentTracker] | None = None) -> None:
        if trackers is None:
            self.trackers: list[ExperimentTracker] = [
                FlightRecorderTracker(),
                MLflowTracker(),
                ResearchEvidenceTracker(),
            ]
        else:
            self.trackers = trackers

    def start_run(self, run_name: str, tags: dict[str, str] | None = None) -> str:
        primary_id = ""
        for tracker in self.trackers:
            run_id = tracker.start_run(run_name=run_name, tags=tags)
            if not primary_id:
                primary_id = run_id
        return primary_id

    def log_params(self, params: dict[str, Any]) -> None:
        for tracker in self.trackers:
            tracker.log_params(params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        for tracker in self.trackers:
            tracker.log_metrics(metrics, step=step)

    def log_state_vector(self, vector: StateVector, step: int | None = None) -> None:
        for tracker in self.trackers:
            tracker.log_state_vector(vector, step=step)

    def log_artifact(self, local_path: str | Path, artifact_type: str = "model") -> str:
        res = ""
        for tracker in self.trackers:
            out = tracker.log_artifact(local_path, artifact_type=artifact_type)
            if not res:
                res = out
        return res

    def log_receipt(self, receipt: LineageReceipt) -> None:
        for tracker in self.trackers:
            tracker.log_receipt(receipt)

    def end_run(self, status: str = "FINISHED") -> None:
        for tracker in self.trackers:
            tracker.end_run(status=status)
