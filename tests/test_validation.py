"""
Unit tests for Shared Validation Layer.
"""

from ckodex_aiops.kernel.domain import DatasetContract
from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease, IntentEnvelope
from ckodex_aiops.validation.validators import (
    AuthorityValidator,
    DataContractValidator,
    ModelIntegrityValidator,
)


def test_authority_validator(sample_intent):
    outcome = AuthorityValidator.validate(sample_intent, required_capability="pipeline:execute")
    assert outcome.admitted
    assert outcome.disposition == "ADMIT_WITH_OBLIGATIONS"

    # Revoked lease should DENY
    revoked_lease = CapabilityLease(capabilities=("pipeline:execute",), revoked=True)
    revoked_intent = IntentEnvelope(
        actor="principal:tester",
        authority=AuthorityPath(tenant="cfyd", workspace="aiops"),
        lease=revoked_lease,
    )
    denied = AuthorityValidator.validate(revoked_intent, required_capability="pipeline:execute")
    assert not denied.admitted
    assert denied.disposition == "DENY"


def test_data_contract_validator(sample_dataframe):
    contract = DatasetContract(
        dataset_name="test_data",
        expected_columns=("id", "feature_a", "feature_b", "target_class"),
        min_rows=10,
        max_null_ratio=0.01,
    )
    outcome = DataContractValidator.validate_polars(sample_dataframe, contract)
    assert outcome.admitted
    assert outcome.disposition == "ADMIT"

    # Failing contract: missing columns
    strict_contract = DatasetContract(
        dataset_name="test_data",
        expected_columns=("id", "non_existent_column"),
        min_rows=10,
    )
    bad_outcome = DataContractValidator.validate_polars(sample_dataframe, strict_contract)
    assert not bad_outcome.admitted
    assert bad_outcome.disposition == "DENY"


def test_model_integrity_validator(temp_workspace):
    dummy_model_file = temp_workspace / "model.pt"
    dummy_model_file.write_bytes(b"dummy-model-weights-binary")

    # Valid
    outcome = ModelIntegrityValidator.validate(dummy_model_file)
    assert outcome.admitted
    sha = outcome.metrics["sha256"]

    # Valid matching hash
    matched = ModelIntegrityValidator.validate(dummy_model_file, expected_sha256=sha)
    assert matched.admitted

    # Tampered hash -> QUARANTINE
    tampered = ModelIntegrityValidator.validate(dummy_model_file, expected_sha256="fakehash0000")
    assert not tampered.admitted
    assert tampered.disposition == "QUARANTINE"
