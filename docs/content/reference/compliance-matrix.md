---
title: "Compliance & Assurance Matrix Reference"
description: "Specification for In-toto SLSA v1.0, NIST SP 800-53 OSCAL, CortAIx CSR 107 controls, and SBOMs."
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
| **CortAIx Factory CSR Matrix** | `data/08_reporting/compliance/cortaix_csr_matrix.json` | `CortaixCsrMatrixGenerator` |

---

## 2. CortAIx CSR 107-Control Traceability

The CortAIx Factory Cybersecurity Requirements (CSR) encompass 107 baseline controls across 12 domains:
1. **AC (Access Control)**: Explicit `CapabilityLease` with automatic epoch expiry.
2. **AU (Audit & Accountability)**: SHA-256 `LineageReceipt` emitted after every node transition.
3. **CA (Security Assessment)**: Multi-dimensional transition conformance suite (`ckodex-aiops conformance`).
4. **CM (Configuration Management)**: Promoted operational baselines with statistical drift verification.
5. **CP (Contingency Planning)**: Designed checkpoints and governed replay with simulation fencing.
6. **IA (Identification & Authentication)**: Authority paths and ambient keyless Sigstore OIDC.
7. **IR (Incident Response)**: Canonical quarantine vault with evidence preservation.
8. **MP (Media Protection)**: Zero-pickle Safetensors checkpoints with memory-mapped read isolation.
9. **RA (Risk Assessment)**: Explicit time-bounded risk derogations (`DerogationRegistry`).
10. **SA (System & Services Acquisition)**: CycloneDX & SPDX SBOM generation parsed from `uv.lock`.
11. **SC (System & Communications)**: Zero-trust secret abstractions and W3C traceparent propagation.
12. **SI (System & Information Integrity)**: Autonomic Day-2 reconciler self-healing loop.
