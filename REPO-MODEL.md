# REPO-MODEL — ckodex-cfyd-aiops @ 9862431
generated: 2026-09-18T22:35:00Z | adapters: codegraph:cli, fallback | coverage: 35/163 (0.215)

## Entry points
- **cli.doctor** (cli) — Day-2 preflight diagnostic inspection of compute, storage, and frameworks `src/ckodex_aiops/cli.py:72`
- **cli.inspect** (cli) — Inspect Lance dataset schemas, row counts, and Safetensors model checkpoints `src/ckodex_aiops/cli.py:197`
- **cli.verify** (cli) — Cryptographic audit of SHA-256 lineage receipts against disk artifacts `src/ckodex_aiops/cli.py:273`
- **cli.run** (cli) — Execute Kedro pipeline DAGs under capability leases with telemetry `src/ckodex_aiops/cli.py:368`
- **cli.profile** (cli) — List, show, and promote operational platform profiles to authoritative baselines `src/ckodex_aiops/cli.py:426`
- **cli.compact** (cli) — Execute distributed fragment compaction and cleanup on Lance datasets `src/ckodex_aiops/cli.py:506`
- **cli.mine** (cli) — Mine Physical AI multimodal robotics telemetry with pushdown SQL filters `src/ckodex_aiops/cli.py:552`
- **cli.reconcile** (cli) — Trigger autonomic Day-2 reconciler loop to detect drift and self-heal `src/ckodex_aiops/cli.py:610`
- **cli.attest** (cli) — Mint in-toto SLSA v1.0 provenance statements with content-addressed digests `src/ckodex_aiops/cli.py:657`
- **cli.oscal** (cli) — Export NIST SP 800-53 Rev 5 OSCAL machine-verifiable component definition `src/ckodex_aiops/cli.py:687`
- **cli.sbom** (cli) — Generate ISO/IEC 5962:2021 SPDX 2.3 and CycloneDX v1.5 JSON SBOM manifests `src/ckodex_aiops/cli.py:705`
- **cli.csr_matrix** (cli) — Export CortAIx Factory CSR 107-control assurance and traceability matrix `src/ckodex_aiops/cli.py:734`
- **cli.onboard** (cli) — Onboard human operator or autonomous agent with capability lease and Hugo runbook `src/ckodex_aiops/cli.py:758`
- **cli.offboard** (cli) — Offboard subject, revoke capability leases, and record audit receipt `src/ckodex_aiops/cli.py:821`
- **cli.airgap_pack** (cli) — Package hermetic air-gap bundle with wheels, docs, models, and checksums `src/ckodex_aiops/cli.py:1083`
- **cli.oci_pack** (cli) — Package repository as OCI Image Layout v1.1.0 artifact with typed layers `src/ckodex_aiops/cli.py:1321`
- **cli.explain** (cli) — Day-2 deep observability answering 11 constitutional operator diagnostic questions `src/ckodex_aiops/cli.py:1455`
- **cli.trace** (cli) — Correlate Telemetry, Execution, Decision, and Evidence truth channels `src/ckodex_aiops/cli.py:1497`
- **cli.recover** (cli) — Reconstruct state and verify cryptographic checkpoint integrity `src/ckodex_aiops/cli.py:1551`
- **cli.replay** (cli) — Governed execution replay under capability lease and side-effect fencing `src/ckodex_aiops/cli.py:1580`
- **cli.quarantine** (cli) — Quarantine suspect artifacts/subjects and preserve immutable evidence `src/ckodex_aiops/cli.py:1632`
- **cli.derogation** (cli) — Explicit risk derogations with compensating controls and expiry `src/ckodex_aiops/cli.py:1718`
- **kedro.pipeline_registry** (lib-export) — Registers Kedro pipeline DAGs: data ingestion, feature engineering, training, eval, inference, physical_ai `src/ckodex_aiops/pipeline_registry.py:20`
- **ci.dagger** (ci) — Dagger hermetic SSDLC engine module configuring containerized CI pipelines `ci/dagger.json:1`
- **ops.justfile** (bin) — Developer task automation recipes for testing, docs, and packaging `justfile:1`

## Module graph

### Direction Rules
- **Pure Semantic Kernel (Rule #6)**: `src/ckodex_aiops/kernel` imports no adapters, no transport, and zero framework SDKs (Ray, Torch, Lance, Kedro, Vault, OTel).
- **Shared Validation (Rule #8)**: `src/ckodex_aiops/validation` imports only from `kernel` and pure schemas; it is never imported by `kernel` and imports no adapters.
- **Transport & Adapters (Rule #9)**: `src/ckodex_aiops/adapters` depend inward on `kernel` and `validation`, translating domain contracts to concrete runtimes without leaking runtime specifics.

### Nodes (by Role)
- **kernel**: `src/ckodex_aiops/kernel/`
- **validation**: `src/ckodex_aiops/validation/`
- **transport**:
  - `adapters.compliance` (`src/ckodex_aiops/adapters/compliance/`)
  - `adapters.distribution` (`src/ckodex_aiops/adapters/distribution/`)
  - `adapters.physical_ai` (`src/ckodex_aiops/adapters/physical_ai/`)
  - `adapters.quantization` (`src/ckodex_aiops/adapters/quantization/`)
  - `adapters.ray_actors` (`src/ckodex_aiops/adapters/ray_actors/`)
  - `adapters.reconciler` (`src/ckodex_aiops/adapters/reconciler/`)
  - `adapters.secrets` (`src/ckodex_aiops/adapters/secrets/`)
  - `adapters.serving` (`src/ckodex_aiops/adapters/serving/`)
  - `adapters.telemetry` (`src/ckodex_aiops/adapters/telemetry/`)
  - `adapters.tracking` (`src/ckodex_aiops/adapters/tracking/`)
- **tool**: `cli` (`src/ckodex_aiops/cli.py`)
- **test**: `tests` (`tests/`)
- **other**: `datasets` (`src/ckodex_aiops/datasets/`), `models` (`src/ckodex_aiops/models/`), `pipelines` (`src/ckodex_aiops/pipelines/`)

### Key Edges
- `validation` → `kernel` (import) `src/ckodex_aiops/validation/validators.py:14`
- `adapters.compliance` → `kernel` (import) `src/ckodex_aiops/adapters/compliance/intoto.py:15`
- `adapters.distribution` → `kernel` (import) `src/ckodex_aiops/adapters/distribution/oci.py:20`
- `adapters.secrets` → `kernel` (import) `src/ckodex_aiops/adapters/secrets/protocol.py:10`
- `pipelines` → `validation` (import) `src/ckodex_aiops/pipelines/data_ingestion/nodes.py:14`
- `pipelines` → `models` (import) `src/ckodex_aiops/pipelines/model_training/nodes.py:15`
- `cli` → `kernel` (import) `src/ckodex_aiops/cli.py:36`
- `cli` → `adapters.compliance` (import) `src/ckodex_aiops/cli.py:25`
- `cli` → `adapters.distribution` (import) `src/ckodex_aiops/cli.py:30`
- `tests` → `kernel` (import) `tests/test_kernel.py:8`
- `tests` → `adapters.distribution` (import) `tests/test_oci.py:11`

## Flows

### FLOW-001 — Intent Admission to Lineage Receipt Lifecycle
trigger: Principal or caller submits execution intent via CLI or API
1. `src/ckodex_aiops/cli.py:368` — `run()` receives pipeline execution intent and initializes runtime context
2. `src/ckodex_aiops/kernel/intent.py:28` — `AuthorityPath` defines standing hierarchy: tenant, workspace, environment, project
3. `src/ckodex_aiops/kernel/intent.py:44` — `CapabilityLease` issues time-bounded, attenuated permissions with expiry timestamp
4. `src/ckodex_aiops/kernel/intent.py:65` — `IntentEnvelope` wraps caller identity, requested capability, lease, and PROPOSED state
5. `src/ckodex_aiops/validation/validators.py:26` — `AuthorityValidator` verifies tenant/workspace validity and unrevoked lease status
6. `src/ckodex_aiops/kernel/intent.py:81` — `IntentEnvelope.transition()` advances envelope lifecycle to ADMITTED
7. `src/ckodex_aiops/kernel/receipt.py:17` — `compute_sha256()` computes cryptographic hashes of inputs and runtime parameters
8. `src/ckodex_aiops/kernel/receipt.py:42` — `LineageReceipt` records immutable execution facts, input/output digests, and authority URN
hidden:
- CapabilityLease automatically expires when epoch exceeds expires_at_epoch (`src/ckodex_aiops/kernel/intent.py:58`)
- AuthorityValidator immediately emits DENY disposition if lease.revoked is True (`src/ckodex_aiops/validation/validators.py:34`)

### FLOW-002 — Model Training & Content-Addressed SLSA Attestation
trigger: Execution of `ckodex-aiops run --pipeline=training` or `kedro run --pipeline=training`
1. `src/ckodex_aiops/cli.py:368` — CLI triggers Kedro session for model_training pipeline
2. `src/ckodex_aiops/pipelines/model_training/nodes.py:21` — `train_representation_model()` splits Lance feature vectors into train/val datasets
3. `src/ckodex_aiops/models/network.py:29` — `VectorRepresentationNet` instantiates PyTorch feedforward network with residual GELU projections
4. `src/ckodex_aiops/models/trainer.py:23` — `ModelTrainer.fit()` runs training epochs with AdamW optimization and validation metrics
5. `src/ckodex_aiops/models/trainer.py:146` — `ModelTrainer.save_checkpoint()` serializes memory-safe model.safetensors and returns SHA-256 digest
6. `src/ckodex_aiops/kernel/receipt.py:23` — `hash_file()` computes content-addressed digest of checkpoint on disk
7. `src/ckodex_aiops/adapters/compliance/intoto.py:24` — `IntotoProvenanceAttestor.generate_attestation()` mints in-toto SLSA v1.0 statement
hidden:
- ModelTrainer dual-saves legacy .pt format alongside zero-copy .safetensors (`src/ckodex_aiops/pipelines/model_training/nodes.py:68`)
- Attestor raises FileNotFoundError before side effects if subject artifact is absent (`src/ckodex_aiops/adapters/compliance/intoto.py:34`)

### FLOW-003 — Autonomic Day-2 Drift Detection & Reconciliation Loop
trigger: Scheduled cron or manual execution of `ckodex-aiops reconcile`
1. `src/ckodex_aiops/cli.py:610` — `reconcile()` instantiates AutonomicReconciler against target baseline profile
2. `src/ckodex_aiops/kernel/reconciler.py:71` — `AutonomicReconciler.observe()` probes Lance dataset fragments, model weights, and runtime health
3. `src/ckodex_aiops/kernel/reconciler.py:111` — `AutonomicReconciler.detect()` detects drift anomalies including FRAGMENT_BLOAT and MISSING_CHECKPOINT
4. `src/ckodex_aiops/kernel/reconciler.py:146` — `AutonomicReconciler.diagnose()` computes 7-dimension StateVector with valence and coherence
5. `src/ckodex_aiops/kernel/state_vector.py:79` — `StateVector.is_healthy()` evaluates anti-dominance invariant where contradictions dominate scores
6. `src/ckodex_aiops/kernel/reconciler.py:41` — `ReconciliationReceipt` computes cryptographic evidence digest of the reconciliation cycle
hidden:
- FRAGMENT_BLOAT (>3 fragment files) automatically triggers dataset compaction (`src/ckodex_aiops/kernel/reconciler.py:117`)
- MISSING_CHECKPOINT anomaly marks auto_healable=False, halting automated recovery for human intervention (`src/ckodex_aiops/kernel/reconciler.py:137`)

### FLOW-004 — OCI Image Layout Packaging & Integrity Verification
trigger: Execution of `ckodex-aiops oci pack --version 1.0.0 --tag latest`
1. `src/ckodex_aiops/cli.py:1321` — `oci_pack()` invokes `OciTemplatePackager.pack_oci_layout` with target version and tag
2. `src/ckodex_aiops/adapters/distribution/oci.py:79` — `create_template_archive()` builds hermetic .tar.gz archive excluding caches and git state
3. `src/ckodex_aiops/adapters/distribution/oci.py:127` — `pack_oci_layout()` creates blobs/sha256/ directory and content-addresses all layers
4. `src/ckodex_aiops/adapters/distribution/oci.py:238` — `inspect_layout()` parses index.json, manifest, config, and verifies layer SHA-256 digests
5. `src/ckodex_aiops/adapters/distribution/oci.py:290` — `unpack_template()` verifies blob digest and safely extracts scaffold to destination directory
hidden:
- Unpack operation strictly enforces filter='data' on Python 3.12+ against path traversal attacks (`src/ckodex_aiops/adapters/distribution/oci.py:315`)
- Unpack verifies blob SHA-256 matches manifest descriptor before extraction (`src/ckodex_aiops/adapters/distribution/oci.py:307`)

## Patterns
- **PAT-001 Pure Semantic Kernel Isolation** — Pure domain logic and state algebra are isolated from all infrastructure, database, and cloud framework SDKs. `src/ckodex_aiops/kernel/intent.py:27`, `src/ckodex_aiops/kernel/state_vector.py:64`
- **PAT-002 Evidence-Bearing Execution Receipts** — Every state mutation or consequential execution emits an immutable, content-addressed LineageReceipt. `src/ckodex_aiops/kernel/receipt.py:42`, `src/ckodex_aiops/kernel/reconciler.py:41`
- **PAT-003 Memory-Safe Secret Value Redaction** — Sensitive credentials are held in non-printing SecretValue containers that redact cleartext and support explicit wipe. `src/ckodex_aiops/adapters/secrets/protocol.py:14`, `src/ckodex_aiops/adapters/secrets/protocol.py:37`
- **PAT-004 Autonomic Day-2 Reconciler Loop** — Continuous convergence of observed technical state back to authoritative promoted baseline profiles. `src/ckodex_aiops/kernel/reconciler.py:61`, `src/ckodex_aiops/kernel/reconciler.py:71`
- **PAT-005 Multi-Layer OCI Image Layout Packaging** — Scaffold and compliance manifests are packaged as typed, content-addressed layers in OCI Image Layout v1.1.0 without daemons. `src/ckodex_aiops/adapters/distribution/oci.py:109`, `src/ckodex_aiops/adapters/distribution/oci.py:238`

## Invariants (conformance vectors)
| id | claim | check | status |
|---|---|---|---|
| INV-001 | kernel module imports zero adapter, transport, or third-party framework dependencies | `! grep -rE "from (ckodex_aiops\.(adapters\|validation\|pipelines\|models)\|ray\|torch\|lance\|kedro\|mlflow\|opentelemetry)" src/ckodex_aiops/kernel/` | green |
| INV-002 | validation module imports no adapters or pipelines | `! grep -rE "from ckodex_aiops\.(adapters\|pipelines)" src/ckodex_aiops/validation/` | green |
| INV-003 | secret values in runtime secrets are never printed or converted to raw strings without redacting | `uv run pytest tests/test_secrets.py -k "test_secret_value_redaction_and_destruction" -q` | green |
| INV-004 | mandatory anti-invariant violations dominate scores and cannot be averaged away | `uv run pytest tests/test_conformance.py -k "test_adversarial_anti_dominance" -q` | green |
| INV-005 | OCI template layout adheres to OCI Image Spec v1.1.0 with zero container daemon requirement | `uv run pytest tests/test_oci.py -q` | green |
| INV-006 | all repository source files satisfy ruff format and linting standards | `uv run ruff check . && uv run ruff format --check .` | green |
| INV-007 | Hugo living documentation compiles cleanly with zero errors and zero warnings | `hugo --source docs --cleanDestinationDir` | green |

## Discrepancies
### DIS-001 [info] Pipeline Registry Default Scope
claimed: README.md:270 suggests physical AI robotics telemetry streaming is an integral pipeline in the platform. `README.md:270` / actual: src/ckodex_aiops/pipeline_registry.py:32 omits physical_ai_pipeline from the default pipeline composition, requiring explicit --pipeline=physical_ai invocation. `src/ckodex_aiops/pipeline_registry.py:32` → accepted-debt

## Do not touch
- **src/ckodex_aiops/kernel/state_vector.py** — Constitutional 7-dimension vector state algebra ($S(e,t) = \langle P, V, A, C, E, L, \tau \rangle$) and anti-dominance invariant enforcement. Modifying these rules compromises mathematical guarantees of non-averaging risk. `src/ckodex_aiops/kernel/state_vector.py:64`
- **src/ckodex_aiops/adapters/secrets/protocol.py** — Memory-safe secret wrapper and redaction boundaries. Any accidental string interpolation or print leakage breaks zero-trust secret protection. `src/ckodex_aiops/adapters/secrets/protocol.py:14`
- **src/ckodex_aiops/kernel/receipt.py** — Cryptographic SHA-256 lineage receipt schema and digest computation. Modifying serialization breaks content-addressed provenance verification. `src/ckodex_aiops/kernel/receipt.py:42`

## Open questions
- Does Ray Actor placement group scheduling (`ray-pg`) on macOS ARM64 Metal provide deterministic memory locality across multiple M-series unified memory clusters without explicit environment affinity flags?
- Should physical AI robotics telemetry streaming be promoted into the Kedro `__default__` pipeline via a conditional runtime feature flag, or remain strictly on-demand?
