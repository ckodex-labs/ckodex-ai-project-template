"""
NIST SP 800-53 Rev 5 OSCAL (Open Security Controls Assessment Language) Generator.
Produces machine-verifiable OSCAL component definitions mapping CKODEX governance
mechanisms directly to NIST controls (CKODEX Rule #10).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class OscalComplianceGenerator:
    """
    Generates OSCAL Component Definition schemas demonstrating compliance with
    federal and enterprise high-assurance controls.
    """

    @classmethod
    def generate_component_definition(cls) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        doc_uuid = str(uuid.uuid4())

        oscal_doc = {
            "component-definition": {
                "uuid": doc_uuid,
                "metadata": {
                    "title": "CKODEX AIOps Platform Security & Integrity Controls",
                    "published": now,
                    "last-modified": now,
                    "version": "1.0.0",
                    "oscal-version": "1.0.4",
                    "remarks": "Automated GAL-1 security controls projection.",
                },
                "components": [
                    {
                        "uuid": str(uuid.uuid4()),
                        "type": "software",
                        "title": "CKODEX AIOps Kernel & Runtime Substrate",
                        "description": "High-assurance Kedro + UV + Ray + Lance + PyTorch execution platform.",
                        "purpose": "Secure execution of distributed AI pretraining, feature engineering, and inference.",
                        "control-implementations": [
                            {
                                "uuid": str(uuid.uuid4()),
                                "source": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                                "description": "NIST SP 800-53 Rev 5 High-Assurance Baseline",
                                "implemented-requirements": [
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "ac-3",
                                        "description": "Access Enforcement: Enforced via Zero-Trust capability leases and memory-safe SecretValue redaction.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "SecretLease & CapabilityLease verification",
                                            },
                                        ],
                                    },
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "au-2",
                                        "description": "Event Logging & 4-Channel Observability: Deep telemetry, execution traces, decision traces, and cryptographic evidence receipts.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "FlightRecorderTracker & W3C TraceContext",
                                            },
                                        ],
                                    },
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "sc-13",
                                        "description": "Cryptographic Protection: SHA-256 content addressing, zero-copy Safetensors format, KMS envelope encryption.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "Safetensors mmap headers & KmsKeyringSecretsAdapter",
                                            },
                                        ],
                                    },
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "si-7",
                                        "description": "Software, Firmware, and Information Integrity: SLSA v1.0 In-toto provenance, Syft SBOM, Grype CVE gating, Gitleaks audit.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "In-toto Statement & Dagger SSDLC module",
                                            },
                                        ],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        }
        return oscal_doc

    @classmethod
    def write_oscal(
        cls, output_path: str | Path = "data/08_reporting/oscal/component_definition.json"
    ) -> Path:
        doc = cls.generate_component_definition()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)
        return out
