"""Tests for Self-Documenting Subject Lifecycle Engine (Onboarding, Offboarding, Audit)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ckodex_aiops.kernel.lifecycle import (
    LifecycleManager,
    LifecycleStatus,
    OffboardingRequest,
    OnboardingRequest,
    SubjectType,
)


@pytest.fixture
def lifecycle_mgr(tmp_path: Path) -> LifecycleManager:
    reg_file = tmp_path / "lifecycle" / "registry.json"
    receipts_dir = tmp_path / "receipts"
    return LifecycleManager(registry_path=reg_file, receipts_dir=receipts_dir)


def test_onboard_operator_and_validate_lease(lifecycle_mgr: LifecycleManager):
    """Must onboard operator with valid capability lease and lineage receipt."""
    req = OnboardingRequest(
        subject_id="engineer-alice",
        subject_type=SubjectType.OPERATOR,
        role="mlops",
        tenant="cfyd",
        workspace="aiops",
        ttl_hours=12.0,
        actor="ciso:security",
    )
    rec = lifecycle_mgr.onboard(req)

    assert rec.subject_id == "engineer-alice"
    assert rec.subject_type == SubjectType.OPERATOR
    assert rec.role == "mlops"
    assert rec.status == LifecycleStatus.ACTIVE
    assert rec.is_active() is True
    assert rec.lease.is_valid() is True
    assert rec.lease.revoked is False
    assert "pipeline:execute" in rec.capabilities
    assert "model:deploy" in rec.capabilities
    assert rec.authority_path.to_urn() == "urn:ckodex:cfyd:aiops:development:ckodex-aiops"

    # Lineage receipt verification
    receipt_file = lifecycle_mgr.receipts_dir / f"{rec.metadata['onboarding_receipt']}.json"
    assert receipt_file.exists()
    receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt_data["node_name"] == "subject:onboard"
    assert receipt_data["authority_urn"] == rec.authority_path.to_urn()


def test_onboard_autonomous_agent(lifecycle_mgr: LifecycleManager):
    """Must onboard autonomous agent with attenuated capabilities."""
    req = OnboardingRequest(
        subject_id="agent-inference-prod",
        subject_type=SubjectType.AGENT,
        role="inference-server",
        ttl_hours=48.0,
    )
    rec = lifecycle_mgr.onboard(req)

    assert rec.subject_type == SubjectType.AGENT
    assert rec.role == "inference-server"
    assert "inference:execute" in rec.capabilities
    assert "pipeline:execute" not in rec.capabilities  # Least authority: inference-only


def test_offboard_subject_revocation(lifecycle_mgr: LifecycleManager):
    """Offboarding must immediately revoke lease, wipe access, and record evidence receipt."""
    # First onboard
    onboard_req = OnboardingRequest(
        subject_id="temp-worker",
        subject_type=SubjectType.OPERATOR,
        role="developer",
    )
    lifecycle_mgr.onboard(onboard_req)

    # Then offboard
    offboard_req = OffboardingRequest(
        subject_id="temp-worker",
        reason="contract ended",
        actor="lead:sre",
    )
    off_rec = lifecycle_mgr.offboard(offboard_req)

    assert off_rec.status == LifecycleStatus.OFFBOARDED
    assert off_rec.is_active() is False
    assert off_rec.lease.is_valid() is False
    assert off_rec.lease.revoked is True
    assert off_rec.offboarding_reason == "contract ended"
    assert off_rec.offboarded_at_utc is not None

    # Verify offboarding receipt
    off_receipt_file = (
        lifecycle_mgr.receipts_dir / f"{off_rec.metadata['offboarding_receipt']}.json"
    )
    assert off_receipt_file.exists()
    off_data = json.loads(off_receipt_file.read_text(encoding="utf-8"))
    assert off_data["node_name"] == "subject:offboard"
    assert off_data["attributes"]["action"] == "OFFBOARD"
    assert off_data["attributes"]["reason"] == "contract ended"


def test_suspend_and_reinstate_lifecycle(lifecycle_mgr: LifecycleManager):
    """Must allow suspending a subject and later reinstating with fresh lease."""
    req = OnboardingRequest(
        subject_id="dev-bob",
        subject_type=SubjectType.OPERATOR,
        role="developer",
    )
    lifecycle_mgr.onboard(req)

    # Suspend
    suspended = lifecycle_mgr.suspend(
        subject_id="dev-bob", reason="security audit hold", actor="sec-team"
    )
    assert suspended.status == LifecycleStatus.SUSPENDED
    assert suspended.is_active() is False
    assert suspended.lease.revoked is True

    # Reinstate
    reinstated = lifecycle_mgr.reinstate(subject_id="dev-bob", actor="sec-team", ttl_hours=24.0)
    assert reinstated.status == LifecycleStatus.ACTIVE
    assert reinstated.is_active() is True
    assert reinstated.lease.is_valid() is True
    assert reinstated.lease.revoked is False


def test_lifecycle_invariants_and_error_handling(lifecycle_mgr: LifecycleManager):
    """Must enforce state transition invariants and reject illegal operations."""
    req = OnboardingRequest(
        subject_id="unique-subject",
        subject_type=SubjectType.OPERATOR,
        role="developer",
    )
    lifecycle_mgr.onboard(req)

    # Cannot re-onboard already active subject
    with pytest.raises(ValueError, match="already actively onboarded"):
        lifecycle_mgr.onboard(req)

    # Cannot offboard non-existent subject
    with pytest.raises(KeyError, match="does not exist in registry"):
        lifecycle_mgr.offboard(OffboardingRequest(subject_id="ghost-user", reason="does not exist"))

    # Offboard once
    lifecycle_mgr.offboard(OffboardingRequest(subject_id="unique-subject", reason="testing"))

    # Cannot offboard twice without force
    with pytest.raises(ValueError, match="already offboarded"):
        lifecycle_mgr.offboard(
            OffboardingRequest(subject_id="unique-subject", reason="repeat offboard")
        )


def test_self_documenting_runbooks_and_hugo_export(lifecycle_mgr: LifecycleManager, tmp_path: Path):
    """Must generate operational runbooks and compile living Hugo documentation."""
    # Onboard subjects
    lifecycle_mgr.onboard(
        OnboardingRequest(
            subject_id="operator-dan",
            subject_type=SubjectType.OPERATOR,
            role="auditor",
        )
    )
    lifecycle_mgr.onboard(
        OnboardingRequest(
            subject_id="agent-batch",
            subject_type=SubjectType.AGENT,
            role="pipeline-executor",
        )
    )
    lifecycle_mgr.offboard(OffboardingRequest(subject_id="agent-batch", reason="decommissioned"))

    # Test Runbook generation
    runbook_text = lifecycle_mgr.generate_runbook(SubjectType.OPERATOR)
    assert "CKODEX Operational Runbook: OPERATOR Lifecycle" in runbook_text
    assert "just doctor" in runbook_text
    assert "just onboard-operator" in runbook_text
    assert "Offboarding & Revocation Procedure" in runbook_text

    # Test Hugo Docs export
    hugo_file = tmp_path / "lifecycle" / "_index.md"
    lifecycle_mgr.export_hugo_docs(output_path=hugo_file)
    assert hugo_file.exists()

    md_content = hugo_file.read_text(encoding="utf-8")
    assert 'title: "Governance & On/Offboarding"' in md_content
    assert "stateDiagram-v2" in md_content
    assert "operator-dan" in md_content
    assert "agent-batch" in md_content
    assert "decommissioned" in md_content
    assert "🟢 ACTIVE" in md_content
