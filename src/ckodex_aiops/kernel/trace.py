"""
Pure Semantic Kernel: Four Truth Channels & Cross-Channel Correlator (Rule #12).
Distinguishes the four orthogonal truth channels:
1. Telemetry trace: What did the machinery do? (CPU, GPU, memory, latency, throughput)
2. Execution trace: Which technical path was actually taken? (node DAG, exit status)
3. Decision trace: On which facts, policies, obligations was the decision based? (StateVectors, validations)
4. Evidence trace: What can we prove afterward? (lineage receipts, cryptographic digests, signatures)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.receipt import compute_sha256
from ckodex_aiops.kernel.state_vector import (
    Anti,
    StateVector,
)


@dataclass(frozen=True)
class TelemetryChannelEntry:
    timestamp_epoch: float
    metric_name: str
    metric_value: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionChannelEntry:
    timestamp_utc: str
    step_name: str
    status: str  # STARTED, COMPLETED, FAILED
    duration_ms: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionChannelEntry:
    timestamp_utc: str
    decision_type: str  # ADMISSION, CONFORMANCE, RECONCILIATION, DEGRADATION
    disposition: str  # ADMIT, DENY, SAFE_HOLD, QUARANTINE
    rules_evaluated: tuple[str, ...]
    state_vector: StateVector
    obligations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvidenceChannelEntry:
    timestamp_utc: str
    evidence_type: str  # RECEIPT, DIGEST, ATTESTATION, CHECKPOINT
    identifier: str
    sha256_digest: str
    uri: str


@dataclass(frozen=True)
class CorrelatedTruthTrace:
    """
    Unified, correlated representation across the four distinct truth channels.
    """

    trace_id: str
    run_id: str
    telemetry_channel: tuple[TelemetryChannelEntry, ...]
    execution_channel: tuple[ExecutionChannelEntry, ...]
    decision_channel: tuple[DecisionChannelEntry, ...]
    evidence_channel: tuple[EvidenceChannelEntry, ...]
    is_coherent: bool = True
    coherence_violations: tuple[str, ...] = field(default_factory=tuple)
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def canonical_digest(self) -> str:
        payload = {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "telemetry_count": len(self.telemetry_channel),
            "execution_count": len(self.execution_channel),
            "decision_count": len(self.decision_channel),
            "evidence_count": len(self.evidence_channel),
            "is_coherent": self.is_coherent,
            "timestamp_utc": self.timestamp_utc,
        }
        return compute_sha256(json.dumps(payload, sort_keys=True))

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "telemetry_count": len(self.telemetry_channel),
            "execution_count": len(self.execution_channel),
            "decision_count": len(self.decision_channel),
            "evidence_count": len(self.evidence_channel),
            "is_coherent": self.is_coherent,
            "coherence_violations": list(self.coherence_violations),
            "timestamp_utc": self.timestamp_utc,
        }


class TruthChannelsCorrelator:
    """
    Correlates telemetry, execution, decisions, and evidence into an auditable trace,
    detecting cross-channel decoherence (Rule #12 & #17).
    """

    def __init__(self, base_reporting_dir: str | Path = "data/08_reporting") -> None:
        self.reporting_dir = Path(base_reporting_dir)

    def correlate(self, run_id_or_prefix: str) -> CorrelatedTruthTrace:
        telemetry: list[TelemetryChannelEntry] = []
        execution: list[ExecutionChannelEntry] = []
        decisions: list[DecisionChannelEntry] = []
        evidence: list[EvidenceChannelEntry] = []
        violations: list[str] = []

        # 1. Search Flight Recorder runs
        fr_dir = self.reporting_dir / "flight_recorder"
        matched_run_dir: Path | None = None
        if fr_dir.exists():
            for rd in fr_dir.glob("run_*"):
                if run_id_or_prefix in rd.name or rd.name in run_id_or_prefix:
                    matched_run_dir = rd
                    break

        if matched_run_dir:
            # Ingest Telemetry
            metrics_file = matched_run_dir / "metrics.jsonl"
            if metrics_file.exists():
                for line in metrics_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        try:
                            d = json.loads(line)
                            for k, v in d.get("metrics", {}).items():
                                telemetry.append(
                                    TelemetryChannelEntry(
                                        timestamp_epoch=float(d.get("timestamp", 0.0)),
                                        metric_name=k,
                                        metric_value=float(v),
                                    )
                                )
                        except Exception:
                            continue

            # Ingest Decisions (State Vectors)
            vectors_file = matched_run_dir / "state_vectors.jsonl"
            if vectors_file.exists():
                for line in vectors_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        try:
                            d = json.loads(line)
                            sv = StateVector(
                                presence=d.get("presence", "PRESENT"),
                                valence=d.get("valence", "POSITIVE"),
                                anti=d.get("anti", "NONE"),
                                coherence=d.get("coherence", "COHERENT"),
                                evidence=d.get("evidence", "VERIFIED"),
                                lifecycle=d.get("lifecycle", "NORMAL"),
                                epoch=float(d.get("epoch", 0.0)),
                                metadata=d.get("metadata", {}),
                            )
                            decisions.append(
                                DecisionChannelEntry(
                                    timestamp_utc=datetime.fromtimestamp(sv.epoch, UTC).isoformat(),
                                    decision_type="STATE_VECTOR_EVALUATION",
                                    disposition="PASS" if sv.is_healthy() else "FAIL",
                                    rules_evaluated=("INVARIANT_ANTI_DOMINANCE",),
                                    state_vector=sv,
                                )
                            )
                        except Exception:
                            continue

        # 2. Ingest Evidence (Receipts)
        receipts_dir = self.reporting_dir / "receipts"
        if receipts_dir.exists():
            for rf in receipts_dir.glob("*.json"):
                try:
                    rdata = json.loads(rf.read_text(encoding="utf-8"))
                    # Filter by run/intent if present
                    if (
                        run_id_or_prefix in rdata.get("receipt_id", "")
                        or run_id_or_prefix in rdata.get("intent_id", "")
                        or run_id_or_prefix in rdata.get("node_name", "")
                        or not matched_run_dir
                    ):
                        evidence.append(
                            EvidenceChannelEntry(
                                timestamp_utc=rdata.get("timestamp_utc", ""),
                                evidence_type="LINEAGE_RECEIPT",
                                identifier=rdata["receipt_id"],
                                sha256_digest=compute_sha256(rf.read_bytes()),
                                uri=str(rf),
                            )
                        )
                        execution.append(
                            ExecutionChannelEntry(
                                timestamp_utc=rdata.get("timestamp_utc", ""),
                                step_name=rdata.get("node_name", "unknown_node"),
                                status="COMPLETED",
                                duration_ms=float(rdata.get("execution_duration_ms", 0.0)),
                                details=rdata.get("attributes", {}),
                            )
                        )
                except Exception:
                    continue

        # 3. Cross-Channel Coherence Verification (Rule #17)
        # Condition A: If execution has failed nodes, decision channel must not indicate purely healthy state
        has_failed_execution = any(e.status == "FAILED" for e in execution)
        if has_failed_execution and all(d.disposition == "PASS" for d in decisions):
            violations.append(
                "Decoherence: Execution reported failure, but decision channel recorded PASS."
            )

        # Condition B: If decision channel reports ANTI violation, evidence trace must not be empty
        has_anti_violation = any(
            d.state_vector.anti in (Anti.ATTACKS, Anti.INVALIDATES) for d in decisions
        )
        if has_anti_violation and not evidence:
            violations.append(
                "Decoherence: ANTI violation was flagged without preserving evidence receipts."
            )

        is_coherent = len(violations) == 0

        return CorrelatedTruthTrace(
            trace_id=f"trace_{compute_sha256(run_id_or_prefix)[:12]}",
            run_id=run_id_or_prefix,
            telemetry_channel=tuple(telemetry),
            execution_channel=tuple(execution),
            decision_channel=tuple(decisions),
            evidence_channel=tuple(evidence),
            is_coherent=is_coherent,
            coherence_violations=tuple(violations),
        )
