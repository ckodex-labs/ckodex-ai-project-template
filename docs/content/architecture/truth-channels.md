---
title: "Four Truth Channels"
description: "Telemetry, Execution, Decision, and Evidence Traces (Rule #12)"
---

## The Four Truth Channels (Rule #12)

Do not collapse all observability into logs. In CKODEX GAL 1, production observability requires four distinct, non-interchangeable truth channels:

```text
┌──────────────────────────────────────────────────────────────┐
│                    FOUR TRUTH CHANNELS                       │
├──────────────────────────────┬───────────────────────────────┤
│ 1. Telemetry Trace           │ 2. Execution Trace            │
│ "What did the machinery do?" │ "Which path was taken?"       │
│ • CPU / GPU utilization      │ • DAG execution order         │
│ • Batch & step latency (p95) │ • Node completion status      │
│ • Queue depth & backpressure │ • Ray RPC actor invocations   │
├──────────────────────────────┼───────────────────────────────┤
│ 3. Decision Trace            │ 4. Evidence Trace             │
│ "On what was this decided?"  │ "What can we prove after?"    │
│ • StateVector S(e,t) algebra │ • Content-addressed SHA-256   │
│ • Validation dispositions    │ • In-toto SLSA v1.0 Statement │
│ • Anti-dominance evaluations │ • Immutable LineageReceipts   │
└──────────────────────────────┴───────────────────────────────┘
```

---

## Cross-Channel Coherence & Decoherence Detection (Rule #17)

A system is **coherent** only when all four truth channels tell a consistent story:
- If **Execution Trace** reports `FAILED`, but **Decision Trace** recorded `PASS`, the system is **decoherent**.
- If an **Anti-invariant violation** occurs, the **Evidence Trace** must contain the immutable receipt proving why the execution was frozen.

### CLI Inspection
```bash
# Correlate all four truth channels for a specific run or receipt
ckodex-aiops trace rcpt_01519ee75d6b
```
