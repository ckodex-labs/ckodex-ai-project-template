"""
MLflow Experiment Tracking & Governance Adapter.
Connects CKODEX telemetry, StateVectors, and Safetensors artifacts directly into MLflow tracking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.receipt import LineageReceipt, compute_sha256
from ckodex_aiops.kernel.state_vector import StateVector


class MLflowTracker:
    """
    MLflow experiment tracking adapter with CKODEX StateVector and Safetensors support.
    """

    def __init__(
        self,
        experiment_name: str = "ckodex_aiops",
        tracking_uri: str | None = None,
    ) -> None:
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        self._mlflow = None
        self._active_run = None
        self._init_mlflow()

    def _init_mlflow(self) -> None:
        try:
            import mlflow

            self._mlflow = mlflow
            if self.tracking_uri:
                mlflow.set_tracking_uri(self.tracking_uri)
            else:
                # Default to local sqlite or file storage inside data/08_reporting/mlruns
                default_mlruns = Path("data/08_reporting/mlruns").absolute()
                default_mlruns.mkdir(parents=True, exist_ok=True)
                mlflow.set_tracking_uri(f"file://{default_mlruns}")

            mlflow.set_experiment(self.experiment_name)
        except Exception:
            self._mlflow = None

    def start_run(self, run_name: str, tags: dict[str, str] | None = None) -> str:
        if self._mlflow is None:
            return "noop_run"

        all_tags = {
            "ckodex.signature": "GAL1",
            "ckodex.kernel": "PURE",
        }
        if tags:
            all_tags.update(tags)

        run = self._mlflow.start_run(run_name=run_name, tags=all_tags)
        self._active_run = run
        return run.info.run_id

    def log_params(self, params: dict[str, Any]) -> None:
        if self._mlflow is None or self._active_run is None:
            return

        # Flatten nested params for MLflow compatibility
        flat_params = {}
        for k, v in params.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    flat_params[f"{k}.{sub_k}"] = str(sub_v)
            else:
                flat_params[k] = str(v)

        self._mlflow.log_params(flat_params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        if self._mlflow is None or self._active_run is None:
            return
        self._mlflow.log_metrics(metrics, step=step)

    def log_state_vector(self, vector: StateVector, step: int | None = None) -> None:
        """
        Logs StateVector as both categorical tags and numerical metric representations.
        """
        if self._mlflow is None or self._active_run is None:
            return

        tags = {
            "state_vector.valence": vector.valence.value,
            "state_vector.anti": vector.anti.value,
            "state_vector.coherence": vector.coherence.value,
            "state_vector.lifecycle": vector.lifecycle.value,
            "state_vector.evidence": vector.evidence.value,
            "state_vector.is_healthy": str(vector.is_healthy()),
        }
        self._mlflow.set_tags(tags)

        # Log numeric representation for metric dashboards
        valence_score = 1.0 if vector.is_healthy() else 0.0
        self._mlflow.log_metric("state_vector_health_score", valence_score, step=step)

    def log_artifact(self, local_path: str | Path, artifact_type: str = "model") -> str:
        if self._mlflow is None or self._active_run is None:
            return ""

        p = Path(local_path)
        if not p.exists():
            return ""

        self._mlflow.log_artifact(str(p), artifact_path=artifact_type)
        digest = compute_sha256(p.read_bytes())
        self._mlflow.set_tag(f"artifact.{p.name}.sha256", digest)
        return str(p)

    def log_receipt(self, receipt: LineageReceipt) -> None:
        if self._mlflow is None or self._active_run is None:
            return

        receipt_path = Path(f"data/08_reporting/receipts/{receipt.receipt_id}.json")
        if receipt_path.exists():
            self._mlflow.log_artifact(str(receipt_path), artifact_path="lineage_receipts")
        self._mlflow.set_tag(f"receipt.{receipt.receipt_id}", receipt.to_digest_string())

    def end_run(self, status: str = "FINISHED") -> None:
        if self._mlflow is not None and self._active_run is not None:
            self._mlflow.end_run(status=status)
            self._active_run = None
