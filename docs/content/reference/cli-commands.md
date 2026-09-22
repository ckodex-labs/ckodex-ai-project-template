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
| `airgap` | Air-Gap hermetic bundle packaging & offline verification | `pack`, `verify` |
| `attest` | Mint In-toto SLSA v1.0 Provenance statement | `--subject`, `--builder` |
| `benchmark` | Run Polars vs Lance vs Ray micro-benchmark | `--num-samples` |
| `cockpit` | Launch interactive terminal UI & export HTML | `--profile`, `--export-html` |
| `config` | Manage typed configuration, schemas & profile overlays | `show`, `validate`, `diff`, `schema`, `init` |
| `conformance` | Evaluate transition conformance suite | None |
| `derogation` | Manage explicit technical risk derogations | `request`, `list`, `revoke`, `evaluate` |
| `doctor` | Preflight diagnostic inspection of hardware & storage | None |
| `drift` | Statistical Wasserstein distance & PSI drift detector | `--baseline`, `--observed` |
| `explain` | Answer 11 constitutional operator diagnostic questions | `TARGET` (argument) |
| `inspect` | Inspect Lance schemas or Safetensors checkpoints | `TARGET` (argument) |
| `integrity` | Content-addressable digestion & Merkle chain verification | `verify`, `digest`, `chain` |
| `lance` | Lance columnar & vector dataset lifecycle operations | `compact`, `optimize`, `mine`, `inspect` |
| `lifecycle` | Inspect subject registry or generate runbooks | `--audit`, `--runbook`, `--export-docs` |
| `oci` | OCI Image Layout packaging & distribution | `pack`, `inspect`, `unpack`, `guide`, `push`, `pull`, `verify` |
| `offboard` | Offboard subject and immediately revoke leases | `--id`, `--reason` |
| `onboard` | Onboard operator, agent, or compute node | `--type`, `--id`, `--role`, `--ttl` |
| `oscal` | Export NIST SP 800-53 Rev 5 OSCAL JSON definition | `--out` |
| `profile` | List, show, or promote platform profiles | `list`, `show`, `promote` |
| `quantize` | Dynamically quantize model weights to Int8 | `--source`, `--out` |
| `quarantine` | Isolate suspect artifacts and preserve evidence | `isolate`, `release`, `list` |
| `ray` | Ray Distributed Computing & Cluster Management | `status`, `start`, `stop`, `pg` |
| `reconcile` | Day-2 autonomic reconciler self-healing loop | `--auto-heal`, `--profile` |
| `recover` | Reconstruct checkpoint and verify disk digests | `--checkpoint`, `--verify-only` |
| `replay` | Governed replay under lease with side-effect fencing | `--receipt`, `--dry-run` |
| `resilience` | Inspect failure budgets, circuit breakers & quarantine vaults | `status`, `trip`, `reset`, `degrade` |
| `run` | Execute Kedro pipeline DAG under capability lease | `--pipeline`, `--profile`, `--ray-address`, `--ray-actors` |
| `sbom` | Generate CycloneDX v1.5 and SPDX 2.3 JSON SBOMs | `--out-dir` |
| `serve` | High-performance Model Serving HTTP Gateway | `--port`, `--model` |
| `trace` | Four Truth Channels, Flight Recorder & Research Evidence | `correlate`, `record`, `summary` |
| `verify` | Audit cryptographic SHA-256 lineage receipts | None |

---

## Rich CLI Help Panels

When executing `uv run ckodex-aiops --help`, commands are categorized into 6 operational panels:

1. **Day-2 Operations & Recovery**: `doctor`, `reconcile`, `cockpit`, `conformance`, `drift`, `recover`, `replay`, `resilience`
2. **Integrity & Observability**: `inspect`, `explain`, `integrity`, `trace`
3. **Governance & Compliance**: `verify`, `attest`, `oscal`, `sbom`, `onboard`, `offboard`, `lifecycle`, `quarantine`, `derogation`
4. **Execution & Pipelines**: `benchmark`, `run`, `quantize`, `serve`, `lance`, `ray`
5. **Configuration & Profiles**: `profile`, `config`
6. **Distribution & Packaging**: `airgap`, `oci`


