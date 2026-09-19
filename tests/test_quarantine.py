"""
Unit and Conformance Tests for Quarantine & Evidence Preservation (Rule #32).
"""

from pathlib import Path

from ckodex_aiops.kernel.quarantine import QuarantineManager, QuarantineStatus


def test_quarantine_isolation_and_release(tmp_path: Path):
    base_dir = tmp_path / "quarantine_base"
    mgr = QuarantineManager(base_dir=base_dir)

    # 1. Create a suspect model artifact
    suspect_file = tmp_path / "compromised_model.safetensors"
    suspect_file.write_bytes(b"corrupted_tensor_data_tampered")

    # 2. Isolate artifact
    rec = mgr.isolate_artifact(
        target_path=suspect_file,
        trigger_anomaly="Model integrity hash check failed",
        target_type="MODEL",
    )

    assert rec.quarantine_id.startswith("quar_")
    assert rec.status == QuarantineStatus.ISOLATED
    assert len(rec.evidence_digests) == 1
    assert rec.canonical_digest() != ""

    vault_file = Path(rec.quarantine_vault_path) / suspect_file.name
    assert vault_file.exists()
    assert vault_file.read_bytes() == b"corrupted_tensor_data_tampered"

    # 3. Add investigation note
    updated = mgr.add_investigation_note(
        rec.quarantine_id, "Triage confirmed corrupt training checkpoint."
    )
    assert updated.status == QuarantineStatus.INVESTIGATING
    assert len(updated.investigation_notes) == 2

    # 4. List quarantined
    active_records = mgr.list_quarantined(active_only=True)
    assert len(active_records) == 1
    assert active_records[0].quarantine_id == rec.quarantine_id

    # 5. Release artifact
    released_rec, receipt = mgr.release(
        rec.quarantine_id, justification="Model retrained from verified source and approved."
    )
    assert released_rec.status == QuarantineStatus.RELEASED
    assert released_rec.release_receipt_id == receipt.receipt_id
    assert receipt.receipt_id.startswith("rcpt_release_")

    # 6. Verify list with active_only=True excludes released
    active_after = mgr.list_quarantined(active_only=True)
    assert len(active_after) == 0

    all_after = mgr.list_quarantined(active_only=False)
    assert len(all_after) == 1
