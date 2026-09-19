---
title: "How to Run Autonomic Day-2 Self-Healing"
description: "Step-by-step guide to detecting drift, fragment bloat, and triggering self-healing reconciliation."
weight: 10
---

# How to Run Autonomic Day-2 Self-Healing

## Goal
Detect divergence between actual storage/model state and the authoritative baseline profile, and execute self-healing convergence without manual intervention.

---

## Procedure

### 1. Identify Target Baseline Profile
Check the available promoted baselines:
```bash
just profile-list
# or: uv run ckodex-aiops profile list
```

### 2. Run Reconciler in Observation Mode (Dry-Run)
Inspect potential drift without executing destructive writes:
```bash
uv run ckodex-aiops reconcile --no-auto-heal
```
If anomalies exist (e.g. `FRAGMENT_BLOAT`, `MISSING_CHECKPOINT`), they will be listed with recommended remediation actions.

### 3. Execute Self-Healing Reconciliation
Trigger automatic convergence:
```bash
just reconcile
# or: uv run ckodex-aiops reconcile --auto-heal
```

### 4. Verify Evidence Receipts
Every reconciliation loop mints a signed `ReconciliationReceipt`:
```bash
ls -la data/08_reporting/receipts/rcpt_reconcile_*
just verify
```
