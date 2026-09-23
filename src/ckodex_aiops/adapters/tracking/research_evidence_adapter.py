"""
CKODEX Research Evidence Protocol Tracker Adapter.
Connects CKODEX AIOps pipelines directly to the Research Evidence Protocol Family (CKX-EXP-001, CKX-RES-001).
Constitutional boundary: Track the experiment, not the world.
Reference resources; do not absorb them.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.receipt import LineageReceipt
from ckodex_aiops.kernel.state_vector import StateVector


class ResearchEvidenceTracker:
    """
    Adapter implementing ExperimentTracker protocol backed by ckodex-research-evidence.
    Maintains pure experiment semantics (trials, factors, observations, evaluations)
    with opaque correlation bindings to models, datasets, and execution receipts.
    """

    @classmethod
    def get_discovery_paths(cls) -> list[Path]:
        paths: list[Path] = []
        if env_path := os.environ.get("CKODEX_RESEARCH_EVIDENCE_PATH"):
            paths.append(Path(env_path))
        paths.append(Path.home() / ".ckodex" / "research-evidence")
        paths.append(Path.home() / "Documents" / "projects" / "operations" / "ckodex-research-evidence")
        return paths

    def __init__(
        self,
        experiment_name: str = "ckx-pipeline-experiment",
        db_path: str | Path | None = None,
        sdk_path: str | Path | None = None,
    ) -> None:
        self.experiment_name = experiment_name
        self.db_path = str(db_path) if db_path else None
        self.sdk_path = sdk_path
        self._sdk_available = False
        self._exp: Any = None
        self._active_trial: Any = None
        self._current_step = 0
        self._init_sdk()

    def _init_sdk(self) -> None:
        # 1. Check if ckx already on python path
        try:
            from ckx import current_or_create  # type: ignore[import-untyped]

            self._create_fn = current_or_create
            self._sdk_available = True
        except ImportError:
            # 2. Try configured or discovery path
            candidate_paths: list[Path] = []
            if self.sdk_path:
                candidate_paths.append(Path(self.sdk_path))
            candidate_paths.extend(self.get_discovery_paths())

            for cand in candidate_paths:
                py_path = cand / "python"
                proto_path = cand / "gen" / "python"
                if py_path.is_dir():
                    if str(py_path) not in sys.path:
                        sys.path.insert(0, str(py_path))
                    if proto_path.is_dir() and str(proto_path) not in sys.path:
                        sys.path.insert(0, str(proto_path))
                    try:
                        from ckx import current_or_create  # type: ignore[import-untyped]

                        self._create_fn = current_or_create
                        self._sdk_available = True
                        break
                    except ImportError:
                        continue

        if self._sdk_available:
            try:
                # If db_path not specified, use local .ckx/research_evidence.db in workspace
                actual_db = (
                    self.db_path
                    or os.environ.get("CKX_RESEARCH_EVIDENCE_DB")
                    or str(Path("data/08_reporting/research_evidence.db").absolute())
                )
                Path(actual_db).parent.mkdir(parents=True, exist_ok=True)
                self._exp = self._create_fn(self.experiment_name, db_path=actual_db)
            except Exception:
                self._sdk_available = False

    @property
    def is_available(self) -> bool:
        """Indicates whether ckodex-research-evidence SDK is loaded and operational."""
        return self._sdk_available and self._exp is not None

    def start_run(self, run_name: str, tags: dict[str, str] | None = None) -> str:
        if not self.is_available:
            return "noop_research_run"

        # In research evidence protocol, run corresponds to a Trial under the frozen experiment revision
        factors = {"run_name": run_name}
        if tags:
            factors.update(tags)

        self._active_trial = self._exp.trial(**factors)
        self._active_trial.__enter__()
        return str(self._active_trial.trial_id)

    def log_params(self, params: dict[str, Any]) -> None:
        if not self.is_available or not self._active_trial:
            return

        # Note annotations or factor assignments
        for k, v in params.items():
            self._active_trial.note(f"parameter:{k}={v}")

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        if not self.is_available or not self._active_trial:
            return

        curr_step = step if step is not None else self._current_step
        self._current_step = curr_step + 1

        for name, value in metrics.items():
            self._active_trial.observe(name, float(value), step=curr_step)

    def log_state_vector(self, vector: StateVector, step: int | None = None) -> None:
        if not self.is_available or not self._active_trial:
            return

        curr_step = step if step is not None else self._current_step
        # Log state vector dimensions as observations
        self._active_trial.observe(f"state_vector.{vector.presence.value}", 1.0, step=curr_step)
        self._active_trial.observe(f"state_vector.{vector.valence.value}", 1.0, step=curr_step)
        self._active_trial.observe(f"state_vector.{vector.coherence.value}", 1.0, step=curr_step)
        self._active_trial.observe(f"state_vector.{vector.lifecycle.value}", 1.0, step=curr_step)

        # Opaque correlation to the vector state digest
        self._active_trial.correlate(
            namespace="ckodex.state_vector",
            kind="vector",
            external_id=f"state_vector:{vector.lifecycle.value}:{vector.valence.value}",
            relation="conformance_disposition",
        )

    def log_artifact(self, local_path: str | Path, artifact_type: str = "model") -> str:
        if not self.is_available or not self._active_trial:
            return str(local_path)

        p = Path(local_path)
        # Constitutional rule #7: Reference != Resource. Opaque correlation only!
        self._active_trial.correlate(
            namespace=f"ckodex.{artifact_type}",
            kind=artifact_type,
            external_id=str(p.name),
            relation="produced_artifact",
        )
        return str(p)

    def log_receipt(self, receipt: LineageReceipt) -> None:
        if not self.is_available or not self._active_trial:
            return

        # Bind opaque correlation to the cryptographic lineage receipt (Rule #6 & #11)
        self._active_trial.correlate(
            namespace="ckodex.receipt",
            kind="lineage_receipt",
            external_id=receipt.receipt_id,
            relation="verified_lineage",
        )
        self._active_trial.note(f"receipt_digest:{receipt.receipt_id}")

    def end_run(self, status: str = "FINISHED") -> None:
        if not self.is_available or not self._active_trial:
            return

        try:
            self._active_trial.__exit__(None, None, None)
        finally:
            self._active_trial = None
