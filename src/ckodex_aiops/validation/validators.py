"""
Shared Deterministic Validators.
Complies with CKODEX Architectural Signature: Shared Validation, Evidence-Bearing.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pyarrow as pa

from ckodex_aiops.kernel.domain import DatasetContract
from ckodex_aiops.kernel.intent import CapabilityLease, IntentEnvelope
from ckodex_aiops.kernel.receipt import compute_sha256
from ckodex_aiops.validation.contracts import ValidationOutcome


class AuthorityValidator:
    """
    Validates IntentEnvelope authority path and CapabilityLease.
    Ensures zero standing privilege: leases must be non-expired, unrevoked, and scoped.
    """

    @staticmethod
    def validate(intent: IntentEnvelope, required_capability: str) -> ValidationOutcome:
        violations: list[str] = []
        obligations: list[str] = []

        if not intent.authority.tenant or not intent.authority.workspace:
            violations.append("Authority path must contain valid tenant and workspace.")

        lease: CapabilityLease = intent.lease
        if lease.revoked:
            violations.append(f"Capability lease '{lease.lease_id}' has been explicitly REVOKED.")

        if not lease.is_valid():
            violations.append(f"Capability lease '{lease.lease_id}' has EXPIRED.")

        if not lease.permits(required_capability):
            violations.append(
                f"Lease '{lease.lease_id}' does not grant required capability: '{required_capability}'."
            )

        if violations:
            return ValidationOutcome(
                admitted=False,
                disposition="DENY",
                violations=violations,
                metrics={"lease_id": lease.lease_id, "required_capability": required_capability},
            )

        obligations.append("EMIT_LINEAGE_RECEIPT_POST_EXECUTION")
        return ValidationOutcome(
            admitted=True,
            disposition="ADMIT_WITH_OBLIGATIONS",
            obligations=obligations,
            metrics={"lease_id": lease.lease_id, "permitted": True},
        )


class DataContractValidator:
    """
    Validates Polars DataFrames and PyArrow Tables against a DatasetContract.
    Checks column presence, row count, null ratios, and vector dimensions.
    """

    @staticmethod
    def validate_polars(df: pl.DataFrame, contract: DatasetContract) -> ValidationOutcome:
        violations: list[str] = []
        metrics: dict[str, float] = {
            "row_count": float(df.height),
            "column_count": float(len(df.columns)),
        }

        # 1. Min rows check
        if df.height < contract.min_rows:
            violations.append(
                f"Dataset '{contract.dataset_name}' row count {df.height} < minimum required {contract.min_rows}."
            )

        # 2. Expected columns check
        missing_cols = [col for col in contract.expected_columns if col not in df.columns]
        if missing_cols:
            violations.append(
                f"Missing required columns in '{contract.dataset_name}': {missing_cols}"
            )

        # 3. Null ratio check
        for col in df.columns:
            null_count = df[col].null_count()
            null_ratio = null_count / max(df.height, 1)
            metrics[f"null_ratio_{col}"] = float(null_ratio)
            if null_ratio > contract.max_null_ratio:
                violations.append(
                    f"Column '{col}' null ratio {null_ratio:.4f} exceeds max allowed {contract.max_null_ratio}."
                )

        # 4. Vector column check
        if contract.vector_column:
            if contract.vector_column not in df.columns:
                violations.append(f"Vector column '{contract.vector_column}' not found.")
            elif contract.vector_dimension and df.height > 0:
                first_vec = df[contract.vector_column][0]
                if hasattr(first_vec, "__len__") and len(first_vec) != contract.vector_dimension:
                    violations.append(
                        f"Vector dimension mismatch: expected {contract.vector_dimension}, got {len(first_vec)}."
                    )

        if violations:
            return ValidationOutcome(
                admitted=False,
                disposition="QUARANTINE" if df.height == 0 else "DENY",
                violations=violations,
                metrics=metrics,
            )

        return ValidationOutcome(
            admitted=True,
            disposition="ADMIT",
            obligations=["VERIFY_SCHEMA_ON_WRITE"],
            metrics=metrics,
        )

    @staticmethod
    def validate_arrow(table: pa.Table, contract: DatasetContract) -> ValidationOutcome:
        df = pl.from_arrow(table)
        assert isinstance(df, pl.DataFrame)
        return DataContractValidator.validate_polars(df, contract)


class ModelIntegrityValidator:
    """
    Verifies cryptographic hash of model file before loading into memory.
    Prevents supply chain contamination and untrusted model deserialization.
    """

    @staticmethod
    def validate(model_path: str | Path, expected_sha256: str | None = None) -> ValidationOutcome:
        path = Path(model_path)
        if not path.exists():
            return ValidationOutcome(
                admitted=False,
                disposition="DENY",
                violations=[f"Model file does not exist: {model_path}"],
            )

        data = path.read_bytes()
        computed_hash = compute_sha256(data)
        metrics = {"file_size_bytes": len(data), "sha256": computed_hash}

        if expected_sha256 and computed_hash != expected_sha256:
            return ValidationOutcome(
                admitted=False,
                disposition="QUARANTINE",
                violations=[
                    f"Model hash mismatch! Expected {expected_sha256}, computed {computed_hash}. Possible tampering."
                ],
                metrics=metrics,
            )

        return ValidationOutcome(
            admitted=True,
            disposition="ADMIT",
            obligations=["AUDIT_MODEL_INSPECTION"],
            metrics=metrics,
        )
