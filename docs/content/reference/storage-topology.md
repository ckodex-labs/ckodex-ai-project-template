---
title: "Storage & Concurrency Topology Reference"
description: "Architecture specification for Lance datasets, secondary IVF-PQ vector indexing, and Ray actor pools."
weight: 50
---

# Storage & Concurrency Topology Reference

---

## 1. Columnar Lance Storage Architecture

The platform uses **Lance** as its native, zero-copy columnar format across raw events, engineered features, and physical AI sensor streams.

### Storage Layout
```text
data/
├── 01_raw/events.lance/            # Raw high-frequency telemetry
├── 04_feature/features.lance/      # Normalized vectors + IVF-PQ indices
└── 04_feature/physical_ai.lance/   # 100 Hz kinematic and robotics telemetry
```

### Key Technical Properties
- **Zero-Copy PyArrow Streaming**: Direct translation between Lance columnar fragments and PyArrow/PyTorch tensors without memory duplication.
- **Pushdown SQL Queries**: Filters evaluated directly in Rust without scanning unselected columns.
- **Distributed Fragment Compaction**: Merges small, high-frequency fragments into large contiguous files to eliminate IOPS degradation.
- **Secondary IVF-PQ Vector Indices**: Inverted File with Product Quantization providing sub-millisecond approximate nearest-neighbor search.

---

## 2. Distributed Ray Concurrency Topology

Compute is orchestrated across a stateful Ray mesh:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        RAY CLUSTER SUBSTRATE                           │
├────────────────────────────────────────────────────────────────────────┤
│ Head Node: GCS Registry • Ray Dashboard (8265) • Plasma Object Store   │
├──────────────────────────────────┬─────────────────────────────────────┤
│ InferenceActor Pool              │ TelemetryCoactor Ring Buffer        │
│ • State: PyTorch Metal / CUDA    │ • Non-blocking queue (max 100k)     │
│ • Dynamic adaptive batching      │ • Fire-and-forget metrics sink      │
│ • Zero-copy plasma memory tensor │ • Prevents backpressure on compute  │
└──────────────────────────────────┴─────────────────────────────────────┘
```

- **Placement Groups**: Gang scheduling allocating bundles atomically (Rule #31: Bounded concurrency).
- **Plasma Object Store**: Zero-copy IPC passing PyArrow tables directly into Ray tasks.
