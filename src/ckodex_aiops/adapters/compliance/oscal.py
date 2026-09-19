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
                        "title": "CKODEX Pure Semantic Kernel",
                        "description": "Zero-dependency deterministic domain invariants and state vector product types S(e,t).",
                        "purpose": "Authoritative intent execution and anti-invariant state evaluation.",
                        "control-implementations": [
                            {
                                "uuid": str(uuid.uuid4()),
                                "source": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                                "description": "NIST SP 800-53 Rev 5 & CortAIx CSR Baseline",
                                "implemented-requirements": [
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "ac-3",
                                        "description": "Access Enforcement: Enforced via Zero-Trust capability leases and intent admission.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "CapabilityLease verification & AuthorityPath",
                                            },
                                            {
                                                "name": "cortaix-csr-control",
                                                "value": "CFY-DSG-ZERO",
                                            },
                                        ],
                                    },
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "au-2",
                                        "description": "Event Logging & 4-Channel Observability: Deep telemetry, execution, decision, and evidence traces.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "LineageReceipt cryptographic SHA-256 digests",
                                            },
                                            {
                                                "name": "cortaix-csr-control",
                                                "value": "INC-LOG-CONS",
                                            },
                                        ],
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "uuid": str(uuid.uuid4()),
                        "type": "software",
                        "title": "CKODEX Zero-Trust Secrets Engine",
                        "description": "Composite secrets manager supporting HashiCorp Vault, cloud KMS, OS keyrings, and Keyless OIDC.",
                        "purpose": "Elimination of static credentials, automatic secret redaction in memory, and dynamic TTL leasing.",
                        "control-implementations": [
                            {
                                "uuid": str(uuid.uuid4()),
                                "source": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                                "description": "NIST SP 800-53 Rev 5 & CortAIx CSR Baseline",
                                "implemented-requirements": [
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "ia-5",
                                        "description": "Authenticator Management: Time-bounded secret leases with automatic destruction.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "SecretValue zeroization & Vault dynamic leases",
                                            },
                                            {"name": "cortaix-csr-control", "value": "CFY-SEC-HAR"},
                                        ],
                                    },
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "sc-13",
                                        "description": "Cryptographic Protection: Envelope encryption using KMS root-of-trust and Safetensors mmap.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "KmsKeyringSecretsAdapter & Safetensors",
                                            },
                                            {
                                                "name": "cortaix-csr-control",
                                                "value": "CFY-CRY-REST",
                                            },
                                        ],
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "uuid": str(uuid.uuid4()),
                        "type": "software",
                        "title": "Dagger SSDLC & Supply-Chain Integrity Engine",
                        "description": "Containerized hermetic CI/CD pipelines producing CycloneDX SBOMs, Grype CVE gating, Gitleaks, and in-toto SLSA provenance.",
                        "purpose": "Continuous assurance and supply-chain non-repudiation.",
                        "control-implementations": [
                            {
                                "uuid": str(uuid.uuid4()),
                                "source": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                                "description": "NIST SP 800-53 Rev 5 & CortAIx CSR Baseline",
                                "implemented-requirements": [
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "si-7",
                                        "description": "Software and Information Integrity: In-toto v1.0 Statement with SLSA Provenance v1.0 attestor.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "IntotoProvenanceAttestor & Syft SBOM",
                                            },
                                            {
                                                "name": "cortaix-csr-control",
                                                "value": "PRR-REL-SBOM",
                                            },
                                        ],
                                    },
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "sa-11",
                                        "description": "Developer Security Testing: Hermetic SAST, DAST, and secret detection gates.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "Dagger module scan_secrets & scan_vulnerabilities",
                                            },
                                            {
                                                "name": "cortaix-csr-control",
                                                "value": "TST-BSL-SAST",
                                            },
                                        ],
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "uuid": str(uuid.uuid4()),
                        "type": "software",
                        "title": "Ray Distributed Concurrency & Lance Storage Mesh",
                        "description": "Stateful Actor/Co-Actor mesh with placement group gang scheduling and zero-copy columnar storage.",
                        "purpose": "High-throughput, memory-safe distributed training and inference.",
                        "control-implementations": [
                            {
                                "uuid": str(uuid.uuid4()),
                                "source": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                                "description": "NIST SP 800-53 Rev 5 & CortAIx CSR Baseline",
                                "implemented-requirements": [
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "sc-5",
                                        "description": "Denial of Service Protection: Bounded ring buffers and non-blocking TelemetryCoactor.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "TelemetryCoactor max_buffer_size backpressure",
                                            },
                                            {"name": "cortaix-csr-control", "value": "CFY-NET-ING"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "uuid": str(uuid.uuid4()),
                        "type": "software",
                        "title": "CKODEX Autonomic Reconciler & Conformance Engine",
                        "description": "Day-2 control loop (OBSERVE -> DETECT -> DIAGNOSE -> RECOVER -> RECONCILE) and multi-dimensional transition tests.",
                        "purpose": "Self-healing storage fragmentation, drift containment, and continuous compliance.",
                        "control-implementations": [
                            {
                                "uuid": str(uuid.uuid4()),
                                "source": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
                                "description": "NIST SP 800-53 Rev 5 & CortAIx CSR Baseline",
                                "implemented-requirements": [
                                    {
                                        "uuid": str(uuid.uuid4()),
                                        "control-id": "si-4",
                                        "description": "Information System Monitoring: Continuous anomaly detection, drift evaluation, and automated healing.",
                                        "props": [
                                            {
                                                "name": "implementation-status",
                                                "value": "implemented",
                                            },
                                            {
                                                "name": "evidence-mechanism",
                                                "value": "AutonomicReconciler & ConformanceEngine",
                                            },
                                            {
                                                "name": "cortaix-csr-control",
                                                "value": "INC-DET-ALER",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
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
