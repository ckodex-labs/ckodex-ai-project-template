"""
In-toto v1.0 Statement & SLSA Provenance v1.0 Attestor.
Binds machine-verifiable content-addressed digests of model artifacts and datasets
to execution receipts and capability leases (CKODEX Rule #39).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ckodex_aiops.kernel.receipt import compute_sha256, hash_file


class IntotoProvenanceAttestor:
    """
    Generates standard In-toto v1.0 Statement containing SLSA Provenance v1.0 predicate.
    """

    @classmethod
    def generate_attestation(
        cls,
        subject_path: str | Path,
        builder_id: str = "https://ckodex.cfyd.ai/builder/gal1-aiops",
        build_type: str = "https://ckodex.cfyd.ai/pipeline/model-training/v1",
        invocation_params: dict[str, Any] | None = None,
        dependencies: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        path = Path(subject_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifact at '{subject_path}' does not exist for attestation.")

        artifact_digest = hash_file(path)
        timestamp = datetime.now(UTC).isoformat()
        invocation_id = f"urn:uuid:{uuid.uuid4()}"

        statement: dict[str, Any] = {
            "_type": "https://in-toto.io/Statement/v1",
            "subject": [
                {
                    "name": str(path),
                    "digest": {
                        "sha256": artifact_digest,
                    },
                }
            ],
            "predicateType": "https://slsa.dev/provenance/v1",
            "predicate": {
                "buildDefinition": {
                    "buildType": build_type,
                    "externalParameters": invocation_params or {},
                    "internalParameters": {
                        "runtime": "python-3.12",
                        "framework": "kedro-lance-ray-pytorch",
                        "assuranceLevel": "GAL-1",
                    },
                    "resolvedDependencies": dependencies or [],
                },
                "runDetails": {
                    "builder": {
                        "id": builder_id,
                        "version": {
                            "ckodex_aiops": "0.1.0",
                        },
                    },
                    "metadata": {
                        "invocationId": invocation_id,
                        "startedOn": timestamp,
                        "finishedOn": timestamp,
                    },
                    "byproducts": [
                        {
                            "name": "receipt_type",
                            "digest": {"sha256": compute_sha256(invocation_id)},
                        }
                    ],
                },
            },
        }
        return statement

    @classmethod
    def write_attestation(cls, statement: dict[str, Any], output_path: str | Path) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(statement, f, indent=2)
        return out
