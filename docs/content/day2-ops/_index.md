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

### 7. Day-2 Autonomic Reconciler (`reconcile`)
Executes the full Day-2 control loop (`OBSERVE -> DETECT -> DIAGNOSE -> RECOVER -> RECONCILE`) to automatically heal fragmentation, model drift, and cluster degradation:
```bash
# Run reconciliation with automated self-healing
uv run ckodex-aiops reconcile --auto-heal

# Dry-run diagnostic check without mutations
uv run ckodex-aiops reconcile --no-auto-heal
```

### 8. Multi-Dimensional Conformance Suite (`conformance`)
Evaluates structural bounds, adversarial ANTI-invariant dominance, and runtime degradation contracts:
```bash
uv run ckodex-aiops conformance
```

### 9. AIOps Mission Cockpit (`cockpit`)
Launches the high-density terminal cockpit or exports a zero-dependency interactive HTML dashboard:
```bash
# Interactive terminal cockpit
uv run ckodex-aiops cockpit

# Export standalone HTML dashboard
uv run ckodex-aiops cockpit --export-html docs/static/cockpit.html
```

### 10. In-toto SLSA Provenance Attestation (`attest`)
Generates machine-verifiable in-toto v1.0 / SLSA Provenance v1.0 statements binding model checkpoints to execution receipts:
```bash
uv run ckodex-aiops attest --subject data/06_models/model.safetensors
```

### 11. NIST SP 800-53 OSCAL Generator (`oscal`)
Exports machine-readable OSCAL component definitions mapping platform safeguards to NIST SP 800-53 controls:
```bash
uv run ckodex-aiops oscal --out data/08_reporting/oscal/component_definition.json
```
