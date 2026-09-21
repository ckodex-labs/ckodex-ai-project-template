---
title: "CLI Command Reference (ckodex-aiops)"
description: "Authoritative command reference for all 32 operations commands in the ckodex-aiops CLI."
weight: 10
---

# CLI Command Reference (`ckodex-aiops`)

Usage:
```bash
uv run ckodex-aiops [COMMAND] [ARGS] [OPTIONS]
# Or via just runner:
just [RECIPE]
```

---

## Complete Command Index

| Command | Synopsis | Key Options |
| :--- | :--- | :--- |
| `airgap-pack` | Package air-gap archive with wheels, docs, models | `--name`, `--out` |
| `airgap-verify` | Verify air-gap bundle offline without network | `--path` |
| `attest` | Mint In-toto SLSA v1.0 Provenance statement | `--subject`, `--builder` |
| `benchmark` | Run Polars vs Lance vs Ray micro-benchmark | `--num-samples` |
| `cockpit` | Launch interactive terminal UI & export HTML | `--profile`, `--export-html` |
| `compact` | Distributed fragment compaction on Lance dataset | `TARGET` (argument) |
| `config` | Manage typed configuration, schemas & profile overlays | `show`, `validate`, `diff`, `schema`, `init` |
| `conformance` | Evaluate transition conformance suite | None |
| `derogation` | Manage explicit technical risk derogations | `create`, `list`, `revoke` |
| `doctor` | Preflight diagnostic inspection of hardware & storage | None |
| `drift` | Statistical Wasserstein distance & PSI drift detector | `--baseline`, `--observed` |
| `explain` | Answer 11 constitutional operator diagnostic questions | `TARGET` (argument) |
| `inspect` | Inspect Lance schemas or Safetensors checkpoints | `TARGET` (argument) |
| `integrity` | Content-addressable digestion & Merkle chain verification | `verify`, `digest` |
| `lifecycle` | Inspect subject registry or generate runbooks | `--audit`, `--runbook`, `--export-docs` |
| `mine` | Physical AI robotics SQL pushdown event mining | `--filter-expr`, `--limit` |
| `oci` | OCI Image Layout packaging & distribution | `pack`, `inspect`, `unpack`, `guide` |
| `offboard` | Offboard subject and immediately revoke leases | `--id`, `--reason` |
| `onboard` | Onboard operator, agent, or compute node | `--type`, `--id`, `--role`, `--ttl` |
| `optimize` | Full lifecycle optimization (compact + cleanup) | `--target` |
| `oscal` | Export NIST SP 800-53 Rev 5 OSCAL JSON definition | `--out` |
| `profile` | List, show, or promote platform profiles | `list`, `show`, `promote` |
| `quantize` | Dynamically quantize model weights to Int8 | `--source`, `--out` |
| `quarantine` | Isolate suspect artifacts and preserve evidence | `isolate`, `release`, `list` |
| `ray-pg` | Allocate Ray Placement Groups for gang scheduling | `--name`, `--num-actors` |
| `reconcile` | Day-2 autonomic reconciler self-healing loop | `--auto-heal`, `--profile` |
| `recover` | Reconstruct checkpoint and verify disk digests | `--checkpoint`, `--verify-only` |
| `replay` | Governed replay under lease with side-effect fencing | `--receipt`, `--dry-run` |
| `resilience` | Inspect failure budgets, circuit breakers & quarantine vaults | `status` |
| `run` | Execute Kedro pipeline DAG under capability lease | `--pipeline`, `--profile` |
| `sbom` | Generate CycloneDX v1.5 and SPDX 2.3 JSON SBOMs | `--out-dir` |
| `serve` | High-performance Model Serving HTTP Gateway | `--port`, `--model` |
| `trace` | Correlate 4 truth channels or inspect flight recorder | `RUN_ID`, `flight-recorder` |
| `verify` | Audit cryptographic SHA-256 lineage receipts | None |

---

## Rich CLI Help Panels

When executing `uv run ckodex-aiops --help`, commands are categorized into 6 operational panels:

1. **Configuration & Profiles**: `config`, `profile`
2. **Execution & Pipelines**: `run`, `serve`, `quantize`, `mine`, `ray-pg`, `benchmark`
3. **Day-2 Operations & Recovery**: `reconcile`, `recover`, `replay`, `quarantine`, `compact`, `optimize`
4. **Integrity & Observability**: `integrity`, `verify`, `drift`, `trace`, `cockpit`, `inspect`
5. **Governance & Compliance**: `doctor`, `conformance`, `explain`, `derogation`, `oscal`, `lifecycle`, `onboard`, `offboard`
6. **Distribution & Packaging**: `airgap-pack`, `airgap-verify`, `oci`, `attest`, `sbom`

