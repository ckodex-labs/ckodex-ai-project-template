---
title: "Observing & Healing Drift with the Day-2 Reconciler"
description: "A hands-on tutorial demonstrating autonomic drift detection and self-healing under the CKODEX Day-2 control loop."
weight: 20
---

# Tutorial: Observing & Healing Drift with the Day-2 Reconciler

In this tutorial, you will observe the canonical Day-2 control loop:
```text
OBSERVE -> DETECT -> DIAGNOSE -> DEGRADE -> CONTAIN -> RECOVER -> VERIFY -> RECONCILE
```

---

## Step 1: Inspect Current System State

Open the platform cockpit or check current profiles:

```bash
just cockpit
```

Verify that the operational state vector $S(e,t)$ displays:
- **Valence**: `POSITIVE`
- **Coherence**: `COHERENT`
- **Lifecycle**: `NORMAL`
- **Anomalies Active**: `0`

---

## Step 2: Evaluate Statistical Drift

Run the statistical feature drift detector to calculate Wasserstein distance and Population Stability Index (PSI):

```bash
just drift
```

The output shows drift scores for all numerical features (e.g. `feature_a`, `feature_b`, `feature_c`, `feature_d`). Because baseline and observed distributions match, all features are reported as `STABLE`.

---

## Step 3: Trigger the Autonomic Reconciler

Trigger the reconciler in dry-run mode or with auto-healing enabled:

```bash
just reconcile
```

The reconciler:
1. **OBSERVES**: Probes Lance dataset fragments, model weight digests, and hardware.
2. **DETECTS**: Compares observed state against active baseline profile `macos_metal_safetensors`.
3. **DIAGNOSES**: Generates a typed `StateVector`.
4. **RECOVERS & RECONCILES**: Automatically compacts unoptimized Lance fragments, checks model presence, and mints an authoritative `ReconciliationReceipt`.

---

## Step 4: Explain the Outcome

Ask the Deep Observability engine to explain what occurred:

```bash
just explain target="data/06_models/model.safetensors"
```

You will see the 11 constitutional operator diagnostic questions answered directly from machine-verifiable evidence.
