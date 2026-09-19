---
title: "Quarantine & Explicit Derogations"
description: "Evidence Preservation during Incidents and Explicit Accepted Risk Engine (Rules #23, #32)"
---

## Quarantine Preserves Evidence (Rule #32)

Quarantine is not merely failure. When a compromised artifact, untrusted model checkpoint, or anomalous telemetry stream is detected, the platform executes:

```text
DETECT -> FREEZE CONSEQUENTIAL EFFECTS -> RESTRICT AUTHORITY/EGRESS ->
PRESERVE RELEVANT STATE -> PRESERVE EVIDENCE -> INVESTIGATE ->
REMEDIATE -> REVALIDATE -> RECOVER OR REVOKE
```

### Quarantine Commands
```bash
# Isolate a suspect model or dataset file
ckodex-aiops quarantine isolate data/06_models/suspect.safetensors -a "Integrity digest mismatch" -t MODEL

# List active quarantined artifacts
ckodex-aiops quarantine list

# Release an artifact after remediation and mint a release receipt
ckodex-aiops quarantine release quar_599ac67b9101 -j "Retrained and verified"
```

---

## Explicit Derogations & Accepted Risk (Rule #23)

Accepted risk does not rewrite history. A derogation binds:
- **Failed Requirement**: Specific control or invariant that was not satisfied.
- **Scope**: Technical blast boundary (e.g. `dev-cluster`).
- **Authority**: Named principal approver.
- **Justification**: Business and technical rationale.
- **Compensating Controls**: Mandatory mitigation controls.
- **Evidence Digest**: Cryptographic hash of input parameters.
- **Expiry**: Hard time limit (never permanent).

### Invariant Rule
> **Never convert FAIL into PASS because someone accepted the risk.**  
> The underlying vector remains truthful.

### Derogation Commands
```bash
# Create an explicit risk derogation
ckodex-aiops derogation create \
  -r "REQ-GPU-DIRECT-IO" \
  -s "apple-silicon-metal" \
  -a "principal:engineer" \
  -j "Apple Silicon unified memory architecture replaces PCIe direct IO" \
  -c "COMPENSATING_METAL_SHADERS" \
  -d 7.0

# List active derogations
ckodex-aiops derogation list

# Revoke a derogation
ckodex-aiops derogation revoke derog_26040d40d08b -r "Hardware refreshed"
```
