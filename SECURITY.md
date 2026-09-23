# Security Policy & Vulnerability Disclosure

## 1. Security Architecture (CKODEX GAL 1)

The **CKODEX AIOps Platform** is engineered according to high-assurance zero-trust principles:
- **Zero Standing Privilege (Rule #2 & #25)**: Execution strictly requires explicit, time-bounded, attenuated `CapabilityLease` instances.
- **Memory-Safe Secrets**: Secrets wrapped in `SecretValue` are scrubbed from heap memory upon lease expiration and redacted in `__repr__` and `__str__`.
- **Zero-Pickle Safetensors (CVE-Resistant)**: Checkpoints use native memory-mapped Safetensors, completely eliminating Python `pickle` deserialization attacks.
- **Supply-Chain Integrity (Rule #39 & NIST SP 800-53 `SI-7`)**: Content-addressed CycloneDX and SPDX SBOMs generated from `uv.lock`, verified with Anchore Grype and signed via In-toto SLSA v1.0.

---

## 2. Reporting a Vulnerability

We take the security of this platform seriously. If you discover a security vulnerability, please follow our coordinated disclosure process:

1. **Do NOT open a public GitHub issue** for security vulnerabilities.
2. Send an encrypted advisory report to: **`security@ckodex.ai`**
3. Include:
   - Description of the vulnerability and attack vector.
   - Affected components (`src/ckodex_aiops/`, `deploy/`, `ci/`).
   - Proof-of-concept (PoC) or reproduction steps.
   - Suggested remediation (if known).

---

## 3. Response Commitments

- **Initial Triage**: Within 24 hours of receipt.
- **Root Cause & Impact Assessment**: Within 72 hours.
- **Fix & Advisory Release**: Coordinated with the reporter before public disclosure.
- **CVE Assignment**: Managed under our CNA partnership.

---

## 4. Supported Versions

| Version | Supported | Security Patch Cadence |
| :--- | :---: | :--- |
| `0.3.x` | Yes | Active release |
| `< 0.3` | No | Upgrade to 0.3.x required |
