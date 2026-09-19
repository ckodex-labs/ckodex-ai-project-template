---
title: "How to Package OCI Artifacts with ORAS and Cosign"
description: "Step-by-step guide to packaging OCI Image Layout v1.1.0 artifacts and distributing via ORAS and Cosign keyless signatures (Rule #39)."
weight: 60
---

# How to Package OCI Artifacts with ORAS and Cosign

## Goal
Package the complete repository scaffold, typed compliance layers (SBOMs, OSCAL, CortAIx CSR), and configuration into an OCI Image Layout v1.1.0 artifact for enterprise container registry distribution.

---

## Procedure

### 1. Package OCI Image Layout Artifact
```bash
just oci-pack version="1.0.0" tag="latest"
# or: uv run ckodex-aiops oci pack --version 1.0.0 --tag latest
```
Creates `dist/oci-template/` containing:
- `index.json` (OCI Layout Spec v1.1.0)
- `oci-layout`
- `blobs/sha256/` (content-addressed tarballs and descriptors)

### 2. Inspect Local OCI Layout
```bash
just oci-inspect
# or: uv run ckodex-aiops oci inspect --layout dist/oci-template
```

### 3. Generate ORAS & Cosign Publishing Commands
```bash
just oci-guide ref="ghcr.io/cfyd-ai/ckodex-aiops-template:v1.0.0"
```
**Output provides:**
- `oras push`: Uploads layout directly to any OCI v1.1-compliant registry (GHCR, ACR, ECR, Harbor).
- `cosign sign`: Attaches keyless Sigstore OIDC cryptographic signature.
- `cosign attest`: Attaches In-toto SLSA provenance predicate.

### 4. Unpack OCI Template into a New Project
```bash
just oci-unpack dest="/path/to/new-project"
```
Instantiates a complete, production-ready workspace from the verified OCI layer.
