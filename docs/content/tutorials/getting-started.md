---
title: "Your First Pipeline & SLSA Attestation"
description: "A step-by-step tutorial taking you through preflight diagnostics, pipeline execution, and minting cryptographic SLSA provenance."
weight: 10
---

# Tutorial: Your First Pipeline & SLSA Attestation

In this tutorial, you will execute a complete machine learning lifecycle under the **CKODEX GAL 1** constitutional governance model.

---

## Prerequisites
- Python 3.12+
- `uv` package manager installed
- Terminal shell (`zsh` or `bash`)

---

## Step 1: Preflight Platform Diagnostics

Before running any computational or mutative workload, verify that your runtime substrate and accelerator are healthy:

```bash
just doctor
# or: uv run ckodex-aiops doctor
```

**Expected Output:**
```text
Subsystem Diagnostics:
• Runtime Host: PASS (Darwin / Linux, Python 3.12.x)
• PyTorch Compute: PASS (Apple Silicon MPS / CUDA active)
• Polars Engine: PASS (16 threads active)
• Lance Vector Storage: PASS
• Ray Runtime: PASS
• Safetensors Engine: PASS
```

---

## Step 2: Run the Ingestion and Feature Extraction Pipeline

Execute the data processing phase using Kedro DAG orchestration:

```bash
just run-pipeline pipeline="data_processing"
```

**What happened:**
1. High-frequency raw events are parsed into a multi-threaded Polars DataFrame.
2. Normalized features are streamed into `data/04_feature/features.lance`.
3. An immutable execution receipt (`rcpt_...`) is minted with SHA-256 digests of all input and output files.

---

## Step 3: Train the PyTorch Representation Model

Train the `VectorRepresentationNet` using accelerated PyTorch tensors:

```bash
just run-pipeline pipeline="training"
```

**What happened:**
1. Lance vector batches stream zero-copy into PyTorch DataLoader.
2. AdamW optimizer trains parameters across epochs.
3. Checkpoints are serialized to zero-copy `data/06_models/model.safetensors` (CVE-safe, zero-pickle).

---

## Step 4: Mint Cryptographic In-toto SLSA v1.0 Provenance

Attest the model artifact using the compliance engine:

```bash
just attest subject="data/06_models/model.safetensors"
```

**What happened:**
1. The subject artifact's SHA-256 is computed.
2. An In-toto v1.0 Statement with SLSA Provenance v1.0 predicate is minted at `data/08_reporting/attestations/`.
3. The attestation records builder identity, materials, external dependencies, and build invocation metadata.

---

## Step 5: Audit All Cryptographic Lineage Receipts

Audit all execution receipts created during this session:

```bash
just verify
```

**Result:**
All execution receipts are verified for cryptographic integrity. You have successfully completed your first governed machine learning lifecycle!
