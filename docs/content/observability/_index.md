---
title: "Observability & OpenTelemetry (OTEL)"
description: "W3C Context Propagation, Four Truth Channels, Flight Recorder & MLflow"
---

## 1. The Four Truth Channels (Rule #12)

Observability is not merely log dumps. The platform enforces four distinct, correlated truth channels:

| Channel | Core Question | Data Representation |
| :--- | :--- | :--- |
| **Telemetry Trace** | *What did the machinery do?* | CPU, GPU, memory, latency, IOPS, backpressure, retry budgets |
| **Execution Trace** | *Which technical path was taken?* | OpenTelemetry Spans, W3C TraceContext, Kedro pipeline nodes, Ray tasks |
| **Decision Trace** | *On which verifiable facts was this decided?* | StateVector transitions, policy digests, contract admissions |
| **Evidence Trace** | *What can we prove afterward?* | Cryptographic SHA-256 LineageReceipts, Safetensors content digests |

---

## 2. OpenTelemetry (OTEL) & Context Propagation

In distributed machine learning, requests move across process boundaries:
`Kedro Node -> Ray Driver -> Ray Worker Pool (InferenceActor / EmbeddingActor) -> Storage`

Without context propagation, distributed traces break, making distributed performance debugging impossible.

### W3C TraceContext Standard
The platform injects and extracts W3C `traceparent` (`version-trace_id-parent_id-trace_flags`):
1. **At Kedro Hook boundary**: Starts the root execution span.
2. **At Ray Actor dispatch**: Serializes carrier dict into the actor call payload.
3. **Inside Ray Actor**: Restores current OpenTelemetry context before executing forward pass on GPU/Metal.
4. **At Receipt Emission**: Binds `trace_id` and `span_id` directly into the immutable `LineageReceipt`.

---

## 3. Dual Observability Substrates

1. **Air-Gap Flight Recorder (Rule #38)**:
   - Local append-only directory at `data/08_reporting/flight_recorder/`.
   - Records privacy-scrubbed JSON manifests, time-series metrics, and state vectors without requiring any network connectivity.

2. **MLflow Tracking Adapter**:
   - Streams parameters, metrics, model artifacts (`model.safetensors`), and state vector tags into centralized MLflow tracking servers.

---

## 4. Ray Actor & Co-Actor Concurrency Pattern (Rule #31)

To eliminate latency spikes on compute-heavy forward passes, telemetry ingest is offloaded to a companion **`TelemetryCoactor`**:
- **`InferenceActor`**: Dedicated to GPU/MPS compute threads. Dispatches telemetry metrics asynchronously via fire-and-forget Ray calls.
- **`TelemetryCoactor`**: Maintains a bounded memory-safe ring buffer, computes rolling percentile latencies, and flushes aggregates without blocking model serving.

---

## 5. AIOps Autonomic Mission Cockpit (Rule #37 & #41)

The platform provides a real-time operator cockpit that integrates all four truth channels into a unified display:
- **State Vector Matrix**: Displays Presence, Valence, Anti, Coherence, Evidence, and Lifecycle in real-time.
- **Lance Storage Topology**: Fragment counts, table versions, and disk consumption.
- **Cryptographic Receipts**: Visual verification DAG of recent pipeline execution receipts.
- **Static HTML Export**: Zero-dependency standalone HTML dashboard exportable to `docs/static/cockpit.html` for offline or web inspection.
