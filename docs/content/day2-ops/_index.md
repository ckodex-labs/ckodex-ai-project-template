---
title: "Day-2 Operations & CLI"
description: "Preflight Diagnostics, Lineage Audits, Profile Selection & Multimodal Mining"
---

## 1. Day-2 by Default (Rule #27 & #28)

A feature is incomplete if it can be deployed but cannot be:
**observed, diagnosed, changed, degraded, contained, quarantined, recovered, replayed, reconciled, rolled back, upgraded, or offboarded.**

---

## 2. Platform CLI Reference (`ckodex-aiops`)

### 1. Preflight Diagnostics (`doctor`)
Runs checks across Apple Silicon Metal (MPS) / NVIDIA CUDA, Polars threads, Lance vector storage, Ray cluster resources, Safetensors engine, and disk capacity:
```bash
uv run ckodex-aiops doctor
```

### 2. Platform Profiles & Baselines (`profile`)
Inspect, select, and promote operating profiles without cookie-cutter duplication:
```bash
# List all candidate profiles and promoted baselines
uv run ckodex-aiops profile list

# Inspect profile configuration and baseline evidence
uv run ckodex-aiops profile show macos_metal_safetensors

# Promote candidate profile to an authoritative baseline
uv run ckodex-aiops profile promote cuda_distributed_pretraining --receipt-id rcpt_cuda_01

# Execute pipeline with profile active
uv run ckodex-aiops run --profile macos_metal_safetensors
```

### 3. Safetensors & Model Inspection (`inspect`)
Inspects Safetensors checkpoints (zero-pickle, mmap), displaying tensor shapes, dtypes, and SHA-256 digests:
```bash
uv run ckodex-aiops inspect data/06_models/model.safetensors
```

### 4. Physical AI Multimodal Event Mining (`mine`)
Applies pushdown SQL filters over high-frequency (100 Hz) robotics telemetry combined with zero-copy Arrow retrieval:
```bash
uv run ckodex-aiops mine --filter-expr "slip_detected = true" --limit 10
```

### 5. Distributed Fragment Compaction (`compact`)
Eliminates small file fragmentation and maximizes read IOPS:
```bash
uv run ckodex-aiops compact data/04_feature/physical_ai.lance
```

### 6. Cryptographic Lineage Audit (`verify`)
Audits all node execution receipts:
```bash
uv run ckodex-aiops verify
```
