---
title: "How to Onboard and Offboard Governed Operators, Agents, and Nodes"
description: "Step-by-step guide to managing the complete lifecycle of governed subjects with capability lease issuance, revocation, and procedural runbooks."
weight: 70
---

# How to Onboard and Offboard Governed Operators, Agents, and Nodes

## Goal
Manage the complete lifecycle of human operators, autonomous AI agents, and compute nodes under zero standing privilege, with automated Hugo procedural documentation.

---

## Procedure

### 1. Onboard a Subject
```bash
# Onboard human operator
just onboard-operator id="op_alice" role="ml-engineer" ttl="24"

# Onboard autonomous AI agent
just onboard-agent id="agent_synthesizer" role="data-pipeline" ttl="12"

# Onboard Ray compute node
just onboard-node id="node_worker_01" role="ray-compute" ttl="48"
```
**Outcome**:
- Authority path validated: `urn:ckodex:cfyd:aiops:development:ckodex-aiops`.
- Scoped, time-bounded `CapabilityLease` issued.
- Procedural Markdown runbook generated.
- Cryptographic onboarding receipt recorded.

### 2. Audit Subject Registry
```bash
just lifecycle-audit
# or: uv run ckodex-aiops lifecycle --audit
```

### 3. Generate Procedural Runbooks
```bash
just lifecycle-runbook type="operator"
```

### 4. Offboard a Subject (Revocation)
```bash
just offboard id="agent_synthesizer" reason="Task completed, revoking leases"
```
**Outcome**:
- Subject status set to `OFFBOARDED`.
- Active `CapabilityLease` is immediately marked `revoked=True`.
- Secret leases wiped.
- Offboarding audit receipt minted in `data/08_reporting/lifecycle/`.
