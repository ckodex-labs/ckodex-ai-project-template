"""
Autonomic Day-2 Reconciler & Self-Healing Engine (CKODEX Rules #28, #33, #35).
Implements the canonical Day-2 control loop:
OBSERVE -> DETECT -> DIAGNOSE -> DEGRADE -> CONTAIN -> RECOVER -> VERIFY -> RECONCILE.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.profiles import PlatformProfile, ProfileRegistry
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


@dataclass
class AnomalyDetection:
    """Detected divergence between observed state and baseline profile."""

    subsystem: str
    anomaly_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    details: dict[str, Any]
    remediation_action: str
    auto_healable: bool = True


@dataclass
class ReconciliationReceipt:
    """Cryptographic evidence of an autonomic reconciliation loop execution."""

    receipt_id: str
    timestamp: float = field(default_factory=lambda: datetime.now(UTC).timestamp())
    initial_vector: StateVector = field(default_factory=StateVector)
    resulting_vector: StateVector = field(default_factory=StateVector)
    anomalies_detected: list[AnomalyDetection] = field(default_factory=list)
    actions_executed: list[str] = field(default_factory=list)
    evidence_digest: str = ""

    def compute_digest(self) -> str:
        payload = (
            f"{self.receipt_id}:{self.timestamp}:{self.initial_vector.lifecycle}:"
            f"{self.resulting_vector.lifecycle}:{','.join(self.actions_executed)}"
        )
        self.evidence_digest = compute_sha256(payload)
        return self.evidence_digest


class AutonomicReconciler:
    """
    Day-2 Reconciliation Engine that continually converges observed state
    back to the authoritative baseline profile.
    """

    def __init__(self, profile_name: str = "macos_metal_safetensors") -> None:
        self.profile_name = profile_name
        self.baseline: PlatformProfile = ProfileRegistry.get_baseline(profile_name)

    def observe(self) -> dict[str, Any]:
        """OBSERVE: Gathers technical state from storage, models, hardware, and runtime."""
        observed: dict[str, Any] = {
            "timestamp": time.time(),
            "profile": self.baseline.name,
            "datasets": {},
            "models": {},
            "runtime": {},
        }

        # Check Lance datasets
        lance_paths = [
            Path("data/01_raw/events.lance"),
            Path("data/04_feature/features.lance"),
            Path("data/04_feature/physical_ai.lance"),
        ]
        for lp in lance_paths:
            if lp.exists():
                data_dir = lp / "data"
                files_count = len(list(data_dir.glob("*.lance"))) if data_dir.exists() else 0
                observed["datasets"][str(lp)] = {
                    "exists": True,
                    "fragment_files": files_count,
                }
            else:
                observed["datasets"][str(lp)] = {"exists": False, "fragment_files": 0}

        # Check model weights
        model_path = Path(self.baseline.model_weights_path)
        if model_path.exists():
            observed["models"][str(model_path)] = {
                "exists": True,
                "size_bytes": model_path.stat().st_size,
                "format": self.baseline.model_format,
            }
        else:
            observed["models"][str(model_path)] = {"exists": False}

        return observed

    def detect(self, observed: dict[str, Any]) -> list[AnomalyDetection]:
        """DETECT: Identifies drift and invariant violations against the baseline."""
        anomalies: list[AnomalyDetection] = []

        # 1. Detect dataset fragmentation
        for path_str, ds_info in observed["datasets"].items():
            if ds_info.get("fragment_files", 0) > 3:
                anomalies.append(
                    AnomalyDetection(
                        subsystem="storage_lance",
                        anomaly_type="FRAGMENT_BLOAT",
                        severity="MEDIUM",
                        details={"dataset": path_str, "fragments": ds_info["fragment_files"]},
                        remediation_action=f"compact_dataset:{path_str}",
                        auto_healable=True,
                    )
                )

        # 2. Detect missing required model weights
        model_path = str(Path(self.baseline.model_weights_path))
        model_info = observed["models"].get(model_path, {})
        if not model_info.get("exists", False):
            anomalies.append(
                AnomalyDetection(
                    subsystem="model_weights",
                    anomaly_type="MISSING_CHECKPOINT",
                    severity="HIGH",
                    details={"model_path": model_path},
                    remediation_action="restore_or_train_model",
                    auto_healable=False,
                )
            )

        return anomalies

    def diagnose(self, anomalies: list[AnomalyDetection]) -> StateVector:
        """DIAGNOSE: Computes operational state vector based on severity."""
        if not anomalies:
            return StateVector(
                presence=Presence.PRESENT,
                valence=Valence.POSITIVE,
                anti=Anti.NONE,
                coherence=Coherence.COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.NORMAL,
                metadata={"status": "All invariants satisfied against baseline."},
            )

        has_critical = any(a.severity == "CRITICAL" for a in anomalies)
        has_high = any(a.severity == "HIGH" for a in anomalies)

        if has_critical:
            return StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEGATIVE,
                anti=Anti.CONTRADICTS,
                coherence=Coherence.DECOHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.SAFE_HOLD,
                metadata={"anomalies_count": len(anomalies)},
            )
        elif has_high:
            return StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEGATIVE,
                anti=Anti.NONE,
                coherence=Coherence.PARTIALLY_COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.DEGRADED,
                metadata={"anomalies_count": len(anomalies)},
            )
        else:
            return StateVector(
                presence=Presence.PRESENT,
                valence=Valence.NEUTRAL,
                anti=Anti.NONE,
                coherence=Coherence.PARTIALLY_COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.DEGRADED,
                metadata={"anomalies_count": len(anomalies)},
            )

    def recover(self, anomalies: list[AnomalyDetection], execute_heal: bool = True) -> list[str]:
        """RECOVER: Executes bounded corrective mutations."""
        actions_taken: list[str] = []

        for anomaly in anomalies:
            if not anomaly.auto_healable and not execute_heal:
                actions_taken.append(f"SKIPPED_MANUAL_REQUIRED:{anomaly.anomaly_type}")
                continue

            if anomaly.anomaly_type == "FRAGMENT_BLOAT" and execute_heal:
                ds_path = anomaly.details["dataset"]
                try:
                    from datetime import timedelta

                    import lance

                    table = lance.dataset(ds_path)
                    table.optimize.compact_files()
                    try:
                        table.cleanup_old_versions(older_than=timedelta(seconds=0))
                    except Exception:
                        pass
                    actions_taken.append(f"HEALED_COMPACTED_FRAGMENTS:{ds_path}")
                except Exception as e:
                    actions_taken.append(f"COMPACTION_FAILED:{ds_path}:{str(e)}")

        return actions_taken

    def run_reconciliation(self, auto_heal: bool = True) -> ReconciliationReceipt:
        """
        Executes full Day-2 Reconciliation loop:
        OBSERVE -> DETECT -> DIAGNOSE -> DEGRADE -> CONTAIN -> RECOVER -> VERIFY -> RECONCILE.
        """
        # 1. Observe
        observed = self.observe()

        # 2. Detect
        anomalies = self.detect(observed)

        # 3. Diagnose (Pre-healing vector)
        pre_vector = self.diagnose(anomalies)

        # 4 & 5. Degrade / Contain / Recover
        actions: list[str] = []
        if anomalies and auto_heal:
            actions = self.recover(anomalies, execute_heal=True)

        # 6. Verify (Post-healing state)
        post_observed = self.observe()
        post_anomalies = self.detect(post_observed)
        post_vector = self.diagnose(post_anomalies)

        if not post_anomalies and actions:
            post_vector = StateVector(
                presence=Presence.PRESENT,
                valence=Valence.POSITIVE,
                anti=Anti.NONE,
                coherence=Coherence.COHERENT,
                evidence=EvidenceStatus.VERIFIED,
                lifecycle=OperationalLifecycle.NORMAL,
                metadata={"reconciled_actions": len(actions)},
            )

        # 7. Reconcile & emit cryptographic receipt
        receipt_id = f"rcpt_reconcile_{int(time.time())}"
        receipt = ReconciliationReceipt(
            receipt_id=receipt_id,
            initial_vector=pre_vector,
            resulting_vector=post_vector,
            anomalies_detected=anomalies,
            actions_executed=actions,
        )
        receipt.compute_digest()
        return receipt
