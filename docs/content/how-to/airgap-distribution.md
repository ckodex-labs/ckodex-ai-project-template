---
title: "How to Package and Verify Air-Gap Bundles"
description: "Step-by-step guide to creating hermetic offline archives and validating SHA-256 manifests without network access (Rule #40)."
weight: 50
---

# How to Package and Verify Air-Gap Bundles

## Goal
Package models, datasets, SLSA attestations, and living documentation into a hermetic, content-addressed archive for deployment into strictly disconnected, air-gapped environments.

---

## Procedure

### 1. Build and Package Air-Gap Bundle
```bash
just airgap-pack
# or: uv run ckodex-aiops airgap-pack \
#   --name "ckodex-aiops-airgap" \
#   --out "data/08_reporting/airgap/bundle.tar.gz"
```
**Contents Packed:**
- Model weights (`data/06_models/model.safetensors`)
- Feature datasets (`data/04_feature/features.lance`)
- Lineage receipts & SLSA v1.0 provenance
- Pre-built HTML documentation site (`docs/public`)
- Hermetic `airgap_manifest.json` containing SHA-256 digests of all bundled files

### 2. Verify Air-Gap Bundle Offline
On the air-gapped target machine (with zero internet access):
```bash
just airgap-verify
# or: uv run ckodex-aiops airgap-verify \
#   --path "data/08_reporting/airgap/bundle.tar.gz"
```
**Verification Outcome:**
Checks that the root SHA-256 matches and every internal archive member matches its individual SHA-256 digest before admission.
