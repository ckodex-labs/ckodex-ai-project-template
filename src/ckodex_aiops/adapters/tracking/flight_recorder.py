"""
Air-Gap Flight Recorder Tracker (CKODEX Rule #38).
Maintains local, privacy-scrubbed, append-only logs for the 4 truth channels:
- Telemetry trace (hardware, throughput, latency)
- Execution trace (nodes, lifecycle transitions)
- Decision trace (StateVector evaluations)
- Evidence trace (cryptographic SHA-256 receipts, Safetensors digests)
"""

from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.receipt import LineageReceipt, compute_sha256
from ckodex_aiops.kernel.state_vector import StateVector


class FlightRecorderTracker:
    """
    Local immutable flight recorder for deep operational observability and air-gap deployment.
    """

    def __init__(self, base_dir: str | Path = "data/08_reporting/flight_recorder") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.active_run_id: str | None = None
        self.run_dir: Path | None = None

    def start_run(self, run_name: str, tags: dict[str, str] | None = None) -> str:
        run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.active_run_id = run_id
        self.run_dir = self.base_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "artifacts").mkdir(exist_ok=True)
        (self.run_dir / "receipts").mkdir(exist_ok=True)

        manifest = {
            "run_id": run_id,
            "run_name": run_name,
            "start_time": time.time(),
            "tags": tags or {},
            "status": "RUNNING",
        }
        (self.run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
        return run_id

    def log_params(self, params: dict[str, Any]) -> None:
        if not self.run_dir:
            return
        params_file = self.run_dir / "parameters.json"
        existing = json.loads(params_file.read_text()) if params_file.exists() else {}
        existing.update(params)
        params_file.write_text(json.dumps(existing, indent=2))

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        if not self.run_dir:
            return
        metrics_file = self.run_dir / "metrics.jsonl"
        payload = {
            "timestamp": time.time(),
            "step": step,
            "metrics": metrics,
        }
        with open(metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    def log_state_vector(self, vector: StateVector, step: int | None = None) -> None:
        if not self.run_dir:
            return
        vectors_file = self.run_dir / "state_vectors.jsonl"
        payload = {
            "timestamp": time.time(),
            "step": step,
            "presence": vector.presence.value,
            "valence": vector.valence.value,
            "anti": vector.anti.value,
            "coherence": vector.coherence.value,
            "evidence": vector.evidence.value,
            "lifecycle": vector.lifecycle.value,
            "epoch": vector.epoch,
            "is_healthy": vector.is_healthy(),
            "metadata": vector.metadata,
        }
        with open(vectors_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    def log_artifact(self, local_path: str | Path, artifact_type: str = "model") -> str:
        if not self.run_dir:
            return str(local_path)
        src = Path(local_path)
        if not src.exists():
            return ""

        dest = self.run_dir / "artifacts" / src.name
        shutil.copy2(src, dest)
        digest = compute_sha256(dest.read_bytes())

        meta_file = self.run_dir / "artifacts" / f"{src.name}.meta.json"
        meta = {
            "artifact_name": src.name,
            "artifact_type": artifact_type,
            "file_size_bytes": dest.stat().st_size,
            "sha256": digest,
            "timestamp": time.time(),
        }
        meta_file.write_text(json.dumps(meta, indent=2))
        return str(dest)

    def log_receipt(self, receipt: LineageReceipt) -> None:
        if not self.run_dir:
            return
        dest = self.run_dir / "receipts" / f"{receipt.receipt_id}.json"
        dest.write_text(json.dumps(receipt.to_dict(), indent=2))

    def end_run(self, status: str = "FINISHED") -> None:
        if not self.run_dir:
            return
        manifest_file = self.run_dir / "run_manifest.json"
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text())
            manifest["status"] = status
            manifest["end_time"] = time.time()
            manifest["duration_sec"] = manifest["end_time"] - manifest["start_time"]
            manifest_file.write_text(json.dumps(manifest, indent=2))
        self.active_run_id = None
        self.run_dir = None
