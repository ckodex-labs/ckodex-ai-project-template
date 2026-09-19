---
title: "How to Execute Governed Replay Under Capability Leases"
description: "Step-by-step guide to executing deterministic, side-effect-fenced replay of historical execution receipts (Rule #34)."
weight: 30
---

# How to Execute Governed Replay Under Capability Leases

## Goal
Reproduce or audit a previous node execution deterministically without risking unintended live state overwrites, under explicit, attenuated authority.

---

## Procedure

### 1. Locate the Source Execution Receipt
Find the receipt ID for the node you wish to replay:
```bash
ls data/08_reporting/receipts/
# Example: rcpt_01519ee75d6b_compute_polars_features_node.json
```

### 2. Execute Fenced Dry-Run Replay
Test the replay in simulation mode with side-effect barriers:
```bash
just replay receipt="rcpt_01519ee75d6b_compute_polars_features_node" dry_run="true"
# or: uv run ckodex-aiops replay --receipt rcpt_01519ee75d6b_compute_polars_features_node --dry-run
```

**Verification:**
The engine checks:
- Caller lease has `pipeline:execute` permission.
- Input digests match original receipt digests.
- Side effects are fenced (`PROHIBIT_DATASET_OVERWRITE`).
- A new `LineageReceipt` is generated tagged with:
  `attributes.is_replay = True` and `attributes.source_receipt_id = "rcpt_..."`.

### 3. Trace the Correlated Replay
Verify cross-channel coherence for the newly minted replay receipt:
```bash
just trace run_id="rcpt_replay_"
```
