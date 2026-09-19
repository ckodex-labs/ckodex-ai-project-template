"""
Unit and Conformance Tests for Deep Observability Explanation Engine (Rule #37).
"""

from pathlib import Path

from ckodex_aiops.kernel.explanation import ExplanationEngine
from ckodex_aiops.kernel.receipt import EvidenceDigest, LineageReceipt


def test_explanation_engine_receipt(tmp_path: Path):
    reporting_dir = tmp_path / "reporting"
    receipts_dir = reporting_dir / "receipts"
    receipts_dir.mkdir(parents=True)

    rcpt = LineageReceipt(
        receipt_id="rcpt_model_train_test",
        intent_id="intent_abc",
        node_name="train_representation_model",
        authority_urn="urn:ckodex:cfyd:aiops:development:ckodex-aiops",
        input_digests=(EvidenceDigest(digest="hash_in", uri="data/04_feature/features.lance"),),
        output_digests=(EvidenceDigest(digest="hash_out", uri="data/06_models/model.safetensors"),),
        execution_duration_ms=125.0,
    )
    (receipts_dir / "rcpt_model_train_test.json").write_text(rcpt.to_json(), encoding="utf-8")

    engine = ExplanationEngine(reporting_dir=reporting_dir)
    report = engine.explain("rcpt_model_train_test")

    assert report.target == "rcpt_model_train_test"
    assert "train_representation_model" in report.what_happened
    assert "model_evaluation" in report.blast_radius
    assert report.is_coherent is True
    assert report.canonical_digest() != ""


def test_explanation_engine_disk_artifact(tmp_path: Path):
    reporting_dir = tmp_path / "reporting"
    reporting_dir.mkdir(parents=True)

    dummy_file = tmp_path / "features.lance"
    dummy_file.write_bytes(b"dummy_features_bytes")

    engine = ExplanationEngine(reporting_dir=reporting_dir)
    report = engine.explain(str(dummy_file))

    assert str(dummy_file) in report.target
    assert "model_training" in report.blast_radius
    assert report.is_coherent is True
