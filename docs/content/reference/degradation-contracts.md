---
title: "Degraded Mode Contracts & Safe Hold Reference"
description: "Specifications for RuntimeMode, ContainmentScope, and DegradedModeContract (Rules #29, #30)."
weight: 30
---

# Degraded Mode Contracts & Safe Hold Reference

Module: `src/ckodex_aiops/kernel/degradation.py`

---

## 1. `RuntimeMode` Enumeration (Rule #29)

Explicit operational lifecycle modes:
- `NORMAL`: All subsystems functioning within nominal parameters.
- `DEGRADED`: Operating under declared residual capabilities; non-critical failures contained.
- `SAFE_HOLD`: Consequential writes and mutative pipelines frozen; diagnostics and audit active.
- `QUARANTINED`: Subject or artifact isolated into quarantine vault.
- `RECOVERING`: Active self-healing reconciliation loop in progress.
- `FAILED`: Terminal unrecoverable condition requiring manual administrative intervention.

---

## 2. `ContainmentScope` Enumeration

- `NONE`: Unrestricted capability envelope.
- `LOCAL_ONLY`: Outbound network egress blocked.
- `PROOF_ONLY`: Execution limited to cryptographic verification and dry-run simulation.
- `READ_ONLY`: Mutative disk writes prohibited; read queries and cached inference allowed.
- `BLOCKED_WRITES`: Dataset modification and model checkpoint updates rejected.
- `QUARANTINE`: Artifact moved to vault; capability leases referencing it revoked.
- `EMERGENCY_REVOKE`: All standing leases terminated immediately.

---

## 3. `DegradedModeContract` Specification (Rule #30)

```python
@dataclass(frozen=True)
class DegradedModeContract:
    contract_id: str
    name: str
    trigger_condition: str
    containment: ContainmentScope
    residual_capabilities: tuple[str, ...]
    prohibited_capabilities: tuple[str, ...]
    freshness_tolerance_seconds: float
    security_guarantees: tuple[str, ...]
    data_integrity_guarantees: tuple[str, ...]
    recovery_criteria: tuple[str, ...]
    max_exposure_window_seconds: float = 3600.0
```

### Pre-Registered Contracts
1. **`dmc-cache-serving`**: Activated upon model drift. Prohibits model updates; permits cached inference.
2. **`dmc-proof-only`**: Activated when remote KMS is unreachable. Prohibits deployment; permits local receipt verification.
3. **`dmc-safe-hold`**: Activated upon ANTI invariant contradiction or decoherence. Freezes all mutations.
