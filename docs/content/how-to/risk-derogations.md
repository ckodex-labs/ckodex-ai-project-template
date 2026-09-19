---
title: "How to Register Explicit Technical Risk Derogations"
description: "Step-by-step guide to recording approved risk derogations with mandatory compensating controls (Rule #23)."
weight: 40
---

# How to Register Explicit Technical Risk Derogations

## Goal
Explicitly bind approved technical risk, scope, approver authority, and mandatory compensating controls without falsifying vector states or converting `FAIL` to `PASS`.

---

## Invariant Rule (Rule #23)
> **Accepted risk does not rewrite history.**  
> A derogation never changes the underlying StateVector from `NEGATIVE` to `POSITIVE`. Instead, it records the accepted risk as an auditable metadata contract with an expiration epoch.

---

## Procedure

### 1. Register a Time-Bounded Derogation
```bash
uv run ckodex-aiops derogation create \
  --requirement "REQ-GPU-DIRECT-IO" \
  --scope "apple-silicon-metal" \
  --approver "principal:lead-architect" \
  --justification "Unified memory architecture on Apple Silicon replaces PCIe direct IO" \
  --control "COMPENSATING_METAL_SHADERS" \
  --control "INT8_QUANTIZATION_FIDELITY_CHECK" \
  --days 14.0
```

### 2. List Active Derogations
```bash
just derogation-list
# or: uv run ckodex-aiops derogation list
```

### 3. Revoke a Derogation Upon Permanent Fix
```bash
uv run ckodex-aiops derogation revoke <derogation_id> \
  --reason "Upgraded hardware to native PCIe Direct IO cluster"
```
Once revoked or expired, the derogation immediately ceases to grant operational tolerance.
