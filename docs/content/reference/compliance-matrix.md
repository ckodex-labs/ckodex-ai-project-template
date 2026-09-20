---
title: "Compliance & Assurance Matrix Reference"
description: "Specification for In-toto SLSA v1.0, NIST SP 800-53 Rev 5 OSCAL, and CycloneDX/SPDX SBOMs."
weight: 40
---

# Compliance & Assurance Matrix Reference

Module: `src/ckodex_aiops/adapters/compliance/`

---

## 1. Supported Compliance Formats

| Standard | Output Path | Generator / Engine |
| :--- | :--- | :--- |
| **In-toto SLSA Provenance v1.0** | `data/08_reporting/attestations/*.json` | `IntotoProvenanceAttestor` |
| **NIST SP 800-53 Rev 5 OSCAL** | `data/08_reporting/oscal/component_definition.json` | `OscalComplianceGenerator` |
| **CycloneDX v1.5 JSON SBOM** | `data/08_reporting/sbom/cyclonedx.json` | `SbomGenerator` |
| **SPDX 2.3 JSON SBOM** | `data/08_reporting/sbom/spdx.json` | `SbomGenerator` |

---

## 2. NIST SP 800-53 Rev 5 Control Families Traceability

The platform enforces and demonstrates machine-verifiable compliance across NIST SP 800-53 Rev 5 control families:
1. **AC (Access Control)**: Explicit `CapabilityLease` with automatic epoch expiry (AC-3, AC-6).
2. **AU (Audit & Accountability)**: SHA-256 `LineageReceipt` emitted after every node transition (AU-2, AU-10).
3. **CA (Security Assessment)**: Multi-dimensional transition conformance suite (`ckodex-aiops conformance`) (CA-2, CA-7).
4. **CM (Configuration Management)**: Promoted operational baselines with statistical drift verification (CM-8).
5. **CP (Contingency Planning)**: Designed checkpoints and governed replay with simulation fencing (CP-9, CP-10).
6. **IA (Identification & Authentication)**: Authority paths and ambient keyless Sigstore OIDC (IA-5).
7. **IR (Incident Response)**: Canonical quarantine vault with evidence preservation (IR-4).
8. **MP (Media Protection)**: Zero-pickle Safetensors checkpoints with memory-mapped read isolation (MP-2).
9. **RA (Risk Assessment)**: Explicit time-bounded risk derogations (`DerogationRegistry`) (RA-3, RA-5).
10. **SA (System & Services Acquisition)**: CycloneDX & SPDX SBOM generation parsed from `uv.lock` (SA-11).
11. **SC (System & Communications)**: Zero-trust secret abstractions and W3C traceparent propagation (SC-5, SC-13, SC-28).
12. **SI (System & Information Integrity)**: Autonomic Day-2 reconciler self-healing loop and SLSA provenance (SI-4, SI-7).
