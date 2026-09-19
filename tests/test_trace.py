"""
Unit and Conformance Tests for Four Truth Channels Correlator (Rule #12).
"""

import json
from pathlib import Path

from ckodex_aiops.kernel.receipt import LineageReceipt
from ckodex_aiops.kernel.trace import TruthChannelsCorrelator


def test_truth_channels_correlation(tmp_path: Path):
    reporting_dir = tmp_path / "reporting"
    fr_dir = reporting_dir / "flight_recorder" / "run_test_123"
    fr_dir.mkdir(parents=True)
    receipts_dir = reporting_dir / "receipts"
    receipts_dir.mkdir(parents=True)

    # 1. Telemetry log
    metrics_file = fr_dir / "metrics.jsonl"
    metrics_file.write_text(
        json.dumps({"timestamp": 1000.0, "metrics": {"cpu_util": 0.45, "latency_ms": 12.4}}) + "\n"
    )

    # 2. Decision log (State vector)
    sv_file = fr_dir / "state_vectors.jsonl"
    sv_file.write_text(
        json.dumps(
            {
                "presence": "PRESENT",
                "valence": "POSITIVE",
                "anti": "NONE",
                "coherence": "COHERENT",
                "evidence": "VERIFIED",
                "lifecycle": "NORMAL",
                "epoch": 1000.0,
            }
        )
        + "\n"
    )

    # 3. Evidence log (Lineage receipt)
    rcpt = LineageReceipt(
        receipt_id="rcpt_run_test_123",
        intent_id="intent_123",
        node_name="model_training_node",
        authority_urn="urn:ckodex:cfyd:aiops:development:ckodex-aiops",
        input_digests=(),
        output_digests=(),
        execution_duration_ms=45.0,
    )
    (receipts_dir / "rcpt_run_test_123.json").write_text(rcpt.to_json(), encoding="utf-8")

    # Correlate
    correlator = TruthChannelsCorrelator(base_reporting_dir=reporting_dir)
    trace = correlator.correlate("run_test_123")

    assert trace.run_id == "run_test_123"
    assert len(trace.telemetry_channel) == 2
    assert len(trace.execution_channel) == 1
    assert len(trace.decision_channel) == 1
    assert len(trace.evidence_channel) == 1
    assert trace.is_coherent is True
    assert trace.canonical_digest() != ""
