---
title: "Explanation & Designed Recovery"
description: "Deep Observability Explanation Engine, Checkpoint Reconstruction, and Governed Replay (Rules #18, #33, #34, #37)"
---

## Deep Observability Must Support Explanation (Rule #37)

A production AI platform must answer the 11 constitutional operator questions:
1. **What happened?** Technical event and duration summary.
2. **Where?** Subsystem and pipeline path.
3. **Why?** Triggering intent and validated capability lease.
4. **Under whose authority?** Standing authority URN hierarchy.
5. **What changed?** Content-addressed output digests and state vector transitions.
6. **What is affected (Blast Radius)?** Downstream consumer DAG dependencies.
7. **Is state coherent?** Cross-channel alignment between decisions and evidence.
8. **Is operation safely degraded?** Adherence to active degraded mode contracts.
9. **What is prohibited?** Capabilities blocked under degraded modes.
10. **Can it recover automatically?** Self-healing eligibility.
11. **Evidence proving diagnosis?** Content-addressed cryptographic receipts.

### CLI Usage
```bash
# Explain a model checkpoint or pipeline step
ckodex-aiops explain data/06_models/model.safetensors

# Explain a specific cryptographic lineage receipt
ckodex-aiops explain rcpt_01519ee75d6b
```

---

## Designed Recovery & Governed Replay (Rules #33, #34)

```text
CHECKPOINT -> FAILURE -> RECONSTRUCT -> VERIFY -> RESUME
```

### Governed Replay Contract
Replay is not blindly resending historical events. Replay requires:
- **Authority**: Must verify active capability lease with `pipeline:execute` permission.
- **Source Evidence**: Must verify the original `LineageReceipt` on disk.
- **Side-Effect Fencing**: Can enforce simulation mode to prevent overwriting production weights.
- **New Receipts**: Emits a new `LineageReceipt` tagged with `is_replay=True`.

```bash
# Verify and recover from a saved checkpoint
ckodex-aiops recover --checkpoint ckpt_1f4c98563c65

# Execute governed replay with dry-run fencing
ckodex-aiops replay --receipt rcpt_01519ee75d6b --dry-run
```
