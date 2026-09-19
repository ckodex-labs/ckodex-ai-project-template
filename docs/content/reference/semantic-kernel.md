---
title: "Semantic Kernel Primitives Reference"
description: "Class specifications, schemas, and algebraic contracts for the Pure Semantic Kernel."
weight: 20
---

# Semantic Kernel Primitives Reference

Module: `src/ckodex_aiops/kernel/`  
Invariant: **Zero Framework Leakage** (no torch, ray, lance, kedro, vault, or otel).

---

## 1. `StateVector`

Typed product state vector $S(e,t) = \langle P, V, A, C, E, L, \tau \rangle$:

```python
@dataclass(frozen=True)
class StateVector:
    presence: Presence = Presence.PRESENT
    valence: Valence = Valence.POSITIVE
    anti: Anti = Anti.NONE
    coherence: Coherence = Coherence.COHERENT
    evidence: EvidenceStatus = EvidenceStatus.VERIFIED
    lifecycle: OperationalLifecycle = OperationalLifecycle.NORMAL
    epoch: float
    metadata: Mapping[str, Any]
```

### Invariant Method: `is_healthy()`
```python
def is_healthy(self) -> bool:
    if self.anti in (Anti.ATTACKS, Anti.INVALIDATES):
        return False
    if self.coherence == Coherence.DECOHERENT:
        return False
    if self.lifecycle in (OperationalLifecycle.FAILED, OperationalLifecycle.QUARANTINED):
        return False
    return self.valence == Valence.POSITIVE
```

---

## 2. `IntentEnvelope` & `CapabilityLease`

```python
@dataclass(frozen=True)
class CapabilityLease:
    lease_id: str
    granted_to: str
    capabilities: tuple[str, ...]
    expires_at_epoch: float
    revoked: bool = False


@dataclass(frozen=True)
class IntentEnvelope:
    intent_id: str
    actor: str
    authority: AuthorityPath
    requested_capability: str
    lease: CapabilityLease
    payload: Mapping[str, Any]
    created_at_utc: str
    lifecycle: IntentLifecycle
```

---

## 3. `LineageReceipt`

```python
@dataclass(frozen=True)
class LineageReceipt:
    receipt_id: str
    intent_id: str
    node_name: str
    authority_urn: str
    input_digests: tuple[EvidenceDigest, ...]
    output_digests: tuple[EvidenceDigest, ...]
    execution_duration_ms: float
    timestamp_utc: str
    attributes: Mapping[str, Any]
```
Method `canonical_digest() -> str` computes SHA-256 over canonical JSON representation.
