---
title: "Vector State Algebra & Anti-Dominance"
description: "Mathematical formulation of Vector State S(e,t), multi-dimensional evidence semantics, and why hard anti-invariants strictly dominate aggregate scoring."
weight: 43
---

# Vector State Algebra & Anti-Dominance

> **Constitutional Rule #13:** Do not model governed reality as merely `PASS` or `FAIL`. Use a typed product vector $S(e,t) = \langle P, V, A, C, E, L, \tau \rangle$.  
> **Constitutional Rule #14:** `EMPTY` is not negative. Absence of evidence is not automatically evidence of failure.  
> **Constitutional Rule #16:** `ANTI` is not "more negative". Anti represents structural opposition and invariant contradiction.  
> **Constitutional Rule #22:** Hard invariants dominate scores. Never average away critical contradictions.

---

## 1. The Fallacy of Boolean Status and Aggregate Percentages

In conventional CI/CD and monitoring tools, compliance and health are collapsed into booleans:
- `status: PASS`
- `healthy: true`
- `compliance_score: 99.2%`

This reductionist approach creates catastrophic blind spots in safety-critical systems:

```text
    99 Passed Unit & Lint Tests
  +  1 Active Cryptographic Signature Forgery (ANTI)
  -------------------------------------------------------
  = 99% PASS  <-- DANGEROUS FALLACY
  = NON-CONFORMANT / CRITICAL BREACH <-- CKODEX TRUTH
```

If an autonomous system passes 99 behavioral tests but fails a single mandatory cryptographic integrity invariant, it is **not** 99% secure. It is completely non-conformant and potentially hostile.

---

## 2. The Vector State Formulation: $S(e,t)$

In CKODEX, the state of any entity $e$ at epoch $t$ is modeled as a 7-tuple product vector:

$$S(e,t) = \langle P, V, A, C, E, L, \tau \rangle$$

Where each coordinate represents an independent semantic dimension:

| Coordinate | Dimension | Type / Canonical Enums | Description |
|:---|:---|:---|:---|
| **$P$** | **Presence** | `EMPTY`, `PRESENT`, `UNKNOWN`, `REDACTED` | Existence status of the evidence or claim. |
| **$V$** | **Valence** | `POSITIVE`, `NEGATIVE`, `NEUTRAL`, `MIXED`, `UNRESOLVED` | Directional support relative to a proposition. |
| **$A$** | **Anti-Relation** | `NONE`, `CONTRADICTS`, `ATTACKS`, `INVALIDATES` | Structural opposition to invariants or claims. |
| **$C$** | **Coherence** | `COHERENT`, `PARTIALLY_COHERENT`, `DECOHERENT`, `RECONCILING` | Agreement across independent truth channels. |
| **$E$** | **Evidence Status** | `UNVERIFIED`, `PROBATIONARY`, `VERIFIED`, `REVOKED` | Cryptographic and procedural assurance level. |
| **$L$** | **Lifecycle / FSM** | `INIT`, `VALIDATING`, `EXECUTING`, `COMPLETED`, `FAILED` | Operational position within the execution FSM. |
| **$\tau$** | **Temporal Epoch** | `ISO-8601 Timestamp + Logical Sequence` | Monotonic clock position of the state observation. |

---

## 3. Presence Semantics: Empty vs. Negative

Constitutional Rule #14 establishes that **Presence is independent of Valence**:
- `EMPTY`: No telemetry or evidence has arrived yet (e.g., waiting for first heartbeat).
- `UNKNOWN`: The system attempted verification, but network isolation prevented a check.
- `REDACTED`: Evidence exists and was verified, but sensitive tenant fields are masked.
- `NEGATIVE`: Evidence was collected, verified, and explicitly disproves the claim.

Treating `UNKNOWN` or `EMPTY` as `NEGATIVE` causes false alarm fatigue and cascading unnecessary failovers. Treating `UNKNOWN` as `POSITIVE` causes silent security bypasses.

---

## 4. Valence vs. Anti-Relations

It is crucial to understand that **`ANTI` is not simply a severe negative valence**:

### Valence ($V$)
Valence measures whether observations satisfy performance or functional thresholds:
- $V = \text{POSITIVE}$: Latency is 12ms (under the 50ms SLA).
- $V = \text{NEGATIVE}$: Latency is 85ms (exceeds the 50ms SLA).

A negative valence indicates degradation or sub-optimal operation, but does not invalidate the identity or trust boundary of the system.

### Anti-Relation ($A$)
Anti represents an **irreconcilable structural contradiction** that shatters system guarantees:
- Artifact claimed to originate from secure build pipeline, but provenance signature is unsigned or signed by unknown authority.
- An executor is actively executing tasks ($L = \text{EXECUTING}$) after its Capability Lease was revoked ($A = \text{INVALIDATES}$).

---

## 5. The Anti-Dominance Scoring Invariant

Let $\mathcal{I} = \{i_1, i_2, \dots, i_n\}$ be the set of mandatory system invariants, and let $\mathcal{M} = \{m_1, m_2, \dots, m_k\}$ be the set of continuous performance metrics.

The aggregate system disposition $D(S)$ is computed using strict **lexicographical domination**:

$$D(S) = \begin{cases}
\text{QUARANTINE} & \text{if } \exists i \in \mathcal{I} \text{ such that } A(i) \in \{\text{ATTACKS}, \text{INVALIDATES}\} \\
\text{SAFE\_HOLD} & \text{if } \exists i \in \mathcal{I} \text{ such that } P(i) = \text{UNKNOWN} \text{ or } C = \text{DECOHERENT} \\
\text{DEGRADED} & \text{if } \forall i \in \mathcal{I}, A(i) = \text{NONE} \text{ and } \exists m \in \mathcal{M} \text{ with } V(m) = \text{NEGATIVE} \\
\text{NORMAL} & \text{if } \forall i \in \mathcal{I}, A(i) = \text{NONE} \text{ and } \forall m \in \mathcal{M}, V(m) = \text{POSITIVE}
\end{cases}$$

### The Axiom of Non-Averaging:
$$\forall k \ge 1, \quad \left( \sum_{j=1}^k \text{POSITIVE}_j \right) \oplus \text{ANTI} \equiv \text{ANTI}$$

No quantity of high performance, fast throughput, or passing test suites can average out a single hard invariant violation. Anti-dominance is implemented directly in `src/ckodex_aiops/kernel/engine.py` to guarantee that the system remains safe under all adversarial conditions.
