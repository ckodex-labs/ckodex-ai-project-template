---
title: "Governance & Resilience Hooks Reference"
description: "Authoritative reference for Enterprise Kedro lifecycle hooks: Authority Admission, Data Integrity, Circuit Breaker, Ray Lifecycle, and Traceability Evidence."
weight: 35
---

# Governance & Resilience Hooks Reference

The `ckx-ai-project-template` integrates five enterprise lifecycle hooks registered directly in Kedro's [`settings.py`](file:///Users/mchorfa/Documents/projects/runbase/ckodex-cfyd-aiops/src/ckodex_aiops/settings.py). These hooks enforce the CKODEX constitutional signature without contaminating pure domain code.

---

## 1. AuthorityAdmissionHook

- **Module**: [`ckodex_aiops.hooks.authority_admission`](file:///Users/mchorfa/Documents/projects/runbase/ckodex-cfyd-aiops/src/ckodex_aiops/hooks/authority_admission.py)
- **Constitutional Rules**: Rule #2 (Authority Precedes Everything), Rule #4 (Intent as Unit of Work), Rule #11 (Proof Before Side Effects), Rule #25 (Zero-Trust Capability Leases).
- **Execution Points**:
  - `before_pipeline_run`: Preflight validation of standing authority and capability lease.
  - `before_node_run`: Fine-grained scope attenuation check per node (`model:train`, `model:evaluate`, `pipeline:execute`).
- **Behavior**:
  - In `strict_mode=True`, missing, expired, or unattenuated leases raise `AdmissionDeniedError`, halting execution before side effects occur.
  - Generates default project intent with 2-hour attenuated lease when none is supplied via environment.

---

## 2. DataIntegrityHook

- **Module**: [`ckodex_aiops.hooks.data_integrity`](file:///Users/mchorfa/Documents/projects/runbase/ckodex-cfyd-aiops/src/ckodex_aiops/hooks/data_integrity.py)
- **Constitutional Rules**: Rule #8 (Shared Validation), Rule #14 (Empty Is Not Negative), Rule #18 (State Lineage).
- **Execution Points**:
  - `before_node_run`: Computes content-addressable digests for all node inputs; halts on unexpected empty data.
  - `after_node_run`: Computes content-addressable digests for all node outputs; scans Polars DataFrames and PyTorch tensors for numerical corruption (NaNs, Infinite values).
- **Digestion Algorithms**:
  - Polars DataFrame: SHA-256 over schema signature, row count, null-count matrix, and per-column contents.
  - PyArrow Table: SHA-256 over schema and arrow column arrays.
  - PyTorch Tensor / Weights: SHA-256 over float byte buffers and state dictionary keys.

---

## 3. ResilienceCircuitBreakerHook

- **Module**: [`ckodex_aiops.hooks.resilience_circuit`](file:///Users/mchorfa/Documents/projects/runbase/ckodex-cfyd-aiops/src/ckodex_aiops/hooks/resilience_circuit.py)
- **Constitutional Rules**: Rule #29 (Runtime Modes), Rule #30 (Degraded Mode Contract), Rule #31 (Bounded Resilience), Rule #32 (Quarantine Preserves Evidence).
- **Execution Points**:
  - `before_node_run`: Checks circuit breaker state (`CLOSED`, `OPEN`, `HALF_OPEN`). Rejects execution if failure budget is exhausted and cooldown timer has not expired.
  - `on_node_error`: Increments failure budget. If threshold (`max_consecutive_failures=3`) is reached, trips the circuit to `OPEN`, isolates failing input payloads into the forensic Quarantine Vault (`data/08_reporting/quarantine/`), and records incident metadata.
  - `after_node_run`: Resets failure counter upon successful execution (completing half-open probe recovery).

---

## 4. TraceabilityEvidenceHook

- **Module**: [`ckodex_aiops.hooks.traceability_evidence`](file:///Users/mchorfa/Documents/projects/runbase/ckodex-cfyd-aiops/src/ckodex_aiops/hooks/traceability_evidence.py)
- **Constitutional Rules**: Rule #10 (Evidence Fabric), Rule #12 (Four Truth Channels), Rule #38 (Flight Recorder).
- **Execution Points**:
  - `before_pipeline_run`: Initializes root W3C TraceContext (`traceparent`).
  - `before_node_run`: Records high-resolution start timestamp and initial process resource usage (`getrusage`).
  - `after_node_run`: Measures CPU user/system time and peak resident memory (`ru_maxrss`). Generates a tamper-evident `LineageReceipt` with parent receipt digest linkage, and appends the event to `data/08_reporting/flight_recorder.jsonl`.

---

## 5. RayLifecycleHook

- **Module**: [`ckodex_aiops.hooks.ray_lifecycle`](file:///Users/mchorfa/Documents/projects/runbase/ckodex-cfyd-aiops/src/ckodex_aiops/hooks/ray_lifecycle.py)
- **Constitutional Rules**: Rule #7 (Runtime Substrate Separation), Rule #37 (Deep Observability).
- **Execution Points**:
  - `before_pipeline_run`: Prewarms the Ray runtime substrate via `RayRuntimeManager.initialize()`, logging available CPU, GPU, and memory resources.
  - `after_pipeline_run`: Flushes asynchronous telemetry buffers in `TelemetryCoactor`.
