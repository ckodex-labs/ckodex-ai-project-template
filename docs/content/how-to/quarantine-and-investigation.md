---
title: "How to Quarantine Suspect Artifacts and Preserve Evidence"
description: "Step-by-step guide to isolating suspect files into the quarantine vault, adding audit notes, and controlled release."
weight: 20
---

# How to Quarantine Suspect Artifacts and Preserve Evidence

## Goal
Immediately isolate a suspect model checkpoint, tainted dataset, or anomalous configuration, freezing its execution egress while cryptographically preserving the exact state for forensic investigation (Rule #32).

---

## Procedure

### 1. Isolate Artifact into Vault
```bash
uv run ckodex-aiops quarantine isolate data/06_models/suspect.safetensors \
  --anomaly "Digest mismatch against SLSA provenance" \
  --type MODEL
```
**Effect**:
- File is copied into `data/08_reporting/quarantine/vault/<quarantine_id>/`.
- Content is hashed with SHA-256 into an immutable `QuarantineRecord`.
- Mutative leases referencing this file are blocked.

### 2. List Active Quarantined Items
```bash
just quarantine-list
# or: uv run ckodex-aiops quarantine list
```

### 3. Record Investigation Notes
Append machine-verifiable notes as triage proceeds:
```bash
uv run python -c "
from ckodex_aiops.kernel.quarantine import QuarantineManager
mgr = QuarantineManager()
mgr.add_investigation_note('<quarantine_id>', 'Confirmed training data contamination from external source.')
"
```

### 4. Release After Remediation
Once retrained or verified, release the artifact back to operational standing:
```bash
uv run ckodex-aiops quarantine release <quarantine_id> \
  --justification "Retrained with clean dataset and verified with SLSA attestor"
```
A new `LineageReceipt` is minted recording the status transition `ISOLATED -> RELEASED`.
