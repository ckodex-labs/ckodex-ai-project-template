"""
Unit and Conformance Tests for Explicit Risk Derogations (Rule #23).
"""

from pathlib import Path

from ckodex_aiops.kernel.derogation import DerogationRegistry


def test_derogation_lifecycle(tmp_path: Path):
    reg = DerogationRegistry(storage_dir=tmp_path)

    # 1. Create derogation
    rec = reg.create_derogation(
        failed_requirement="REQ-SECURITY-MUTUAL-TLS",
        scope="local-test-cluster",
        approver="principal:security-lead",
        justification="Local testing environment does not terminate external traffic",
        compensating_controls=["EPHEMERAL_TOKEN_AUTH", "LOCALHOST_BINDING"],
        evidence_digest="sha256:1234567890abcdef",
        duration_days=2.0,
    )

    assert rec.derogation_id.startswith("derog_")
    assert rec.is_valid() is True
    assert rec.failed_requirement == "REQ-SECURITY-MUTUAL-TLS"
    assert "EPHEMERAL_TOKEN_AUTH" in rec.compensating_controls
    assert rec.canonical_digest() != ""

    # 2. Get derogation
    fetched = reg.get_derogation(rec.derogation_id)
    assert fetched is not None
    assert fetched.derogation_id == rec.derogation_id
    assert fetched.is_valid() is True

    # 3. List derogations
    active_list = reg.list_derogations(active_only=True)
    assert len(active_list) == 1
    assert active_list[0].derogation_id == rec.derogation_id

    # 4. Audit
    audit = reg.audit_derogations()
    assert audit["total_derogations"] == 1
    assert audit["active_derogations"] == 1
    assert audit["expired_or_revoked_derogations"] == 0

    # 5. Revoke derogation
    revoked = reg.revoke_derogation(rec.derogation_id, reason="Security audit completed")
    assert revoked.is_valid() is False
    assert revoked.active is False
    assert "REVOKED" in revoked.justification

    # Verify audit reflects revocation
    audit_after = reg.audit_derogations()
    assert audit_after["active_derogations"] == 0
    assert audit_after["expired_or_revoked_derogations"] == 1
