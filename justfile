# CKODEX AIOps Platform — Modern Justfile
# Constitutional: GAL 1
# Usage: just <recipe>

set shell := ["bash", "-cu"]
set dotenv-load := true

# Default recipe: list available commands
default:
    @just --list

# ==============================================================================
# Development & Quality Assurance
# ==============================================================================

# Install project dependencies with UV
install:
    uv sync

# Verify or refresh UV deterministic lockfile
sync:
    uv lock --check || uv lock

# Run full pytest test suite
test *args="":
    uv run pytest -v {{args}}

# Run fast unit tests only
test-fast:
    uv run pytest -v -m "not slow" -k "not ray and not lance_ray"

# Run Ruff linter across codebase
lint:
    uv run ruff check .

# Run Ruff code formatter
format:
    uv run ruff format . && uv run ruff check . --fix

# Run type checker
typecheck:
    uv run mypy src/ckodex_aiops

# Build or update CocoIndex Code semantic index
ccc-index:
    ccc index

# Search codebase semantically using CocoIndex Code
ccc-search query:
    ccc search "{{query}}"

# ==============================================================================
# Day-2 Operations & AIOps Control Plane
# ==============================================================================

# Run Day-2 platform preflight health diagnostics
doctor:
    uv run ckodex-aiops doctor

# Execute full Kedro end-to-end pipeline DAG
run-pipeline pipeline="__default__":
    uv run ckodex-aiops run --pipeline {{pipeline}}

# Run autonomic self-healing reconciler loop
reconcile:
    uv run ckodex-aiops reconcile --auto-heal

# Run multi-dimensional transition conformance evaluation
conformance:
    uv run ckodex-aiops conformance

# Run statistical feature and sensor drift detection
drift:
    uv run ckodex-aiops drift

# Run high-throughput micro-benchmark (Polars vs Lance vs Ray)
benchmark samples="5000":
    uv run ckodex-aiops benchmark --num-samples {{samples}}

# Launch interactive terminal Mission Cockpit and export HTML
cockpit:
    uv run ckodex-aiops cockpit --export-html docs/static/cockpit.html

# Launch zero-copy Model Serving HTTP Gateway
serve port="8080" model="data/06_models/model.safetensors":
    uv run ckodex-aiops serve --port {{port}} --model {{model}}

# Dynamically quantize Safetensors model weights to Int8
quantize source="data/06_models/model.safetensors" out="data/06_models/model_int8.pt":
    uv run ckodex-aiops quantize --source {{source}} --out {{out}}

# Execute full lifecycle optimization on Lance dataset (compaction + prune)
optimize target="data/04_feature/features.lance":
    uv run ckodex-aiops optimize --target {{target}}

# Allocate and inspect Ray Placement Groups for atomic gang scheduling
ray-pg name="infer_pg" actors="2":
    uv run ckodex-aiops ray-pg --name {{name}} --num-actors {{actors}}

# Mine Physical AI multimodal robotics sensor telemetry with pushdown SQL
mine filter="slip_detected = true" limit="10":
    uv run ckodex-aiops mine --filter-expr "{{filter}}" --limit {{limit}}

# Compact distributed Lance dataset fragments
compact target="data/04_feature/physical_ai.lance":
    uv run ckodex-aiops compact {{target}}

# Audit cryptographic SHA-256 lineage receipts
verify:
    uv run ckodex-aiops verify

# List platform profiles and promoted baselines
profile-list:
    uv run ckodex-aiops profile list

# ==============================================================================
# Compliance, Supply Chain & CortAIx CSR
# ==============================================================================

# Generate CycloneDX and SPDX Software Bill of Materials (SBOM)
sbom:
    uv run ckodex-aiops sbom --out-dir data/08_reporting/sbom

# Generate NIST SP 800-53 Rev 5 & CortAIx CSR OSCAL Component Definition
oscal:
    uv run ckodex-aiops oscal --out data/08_reporting/oscal/component_definition.json

# Mint cryptographic In-toto SLSA v1.0 Provenance statement
attest subject="data/06_models/model.safetensors":
    uv run ckodex-aiops attest --subject {{subject}}

# Generate CortAIx CSR (Cybersecurity Requirements) Traceability Matrix
csr-matrix:
    uv run ckodex-aiops csr-matrix --out-dir data/08_reporting/compliance

# Package hermetic, content-addressed air-gap distribution archive
airgap-pack name="ckodex-aiops-production" out="data/08_reporting/airgap/bundle.tar.gz":
    uv run ckodex-aiops airgap-pack --name {{name}} --out {{out}}

# Verify air-gap distribution bundle integrity and SHA-256 manifests offline
airgap-verify bundle="data/08_reporting/airgap/bundle.tar.gz":
    uv run ckodex-aiops airgap-verify --path {{bundle}}

# ==============================================================================
# Governance, Authority & Subject Lifecycle (On/Offboarding)
# ==============================================================================

# Onboard a human operator with bounded capability lease
onboard-operator id role="developer" ttl="24":
    uv run ckodex-aiops onboard --type operator --id {{id}} --role {{role}} --ttl {{ttl}}

# Onboard an autonomous AI agent with attenuated permissions
onboard-agent id role="pipeline-executor" ttl="24":
    uv run ckodex-aiops onboard --type agent --id {{id}} --role {{role}} --ttl {{ttl}}

# Onboard a compute node into the Ray cluster
onboard-node id role="ray-worker" ttl="24":
    uv run ckodex-aiops onboard --type compute-node --id {{id}} --role {{role}} --ttl {{ttl}}

# Offboard a governed subject (immediate lease revocation and secret wipe)
offboard id reason="operational rotation":
    uv run ckodex-aiops offboard --id {{id}} --reason "{{reason}}"

# Audit governed subject lifecycle registry and cryptographic receipts
lifecycle-audit:
    uv run ckodex-aiops lifecycle --audit

# Generate self-documenting procedural runbook (operator, agent, node)
lifecycle-runbook type="operator":
    uv run ckodex-aiops lifecycle --runbook {{type}}

# Compile and export living Hugo documentation for lifecycle
lifecycle-docs:
    uv run ckodex-aiops lifecycle --export-docs

# ==============================================================================
# Containers & Local Compose Stack
# ==============================================================================

# Launch full local stack with Docker Compose (Ray, MLflow, Vault, Gateway, Cockpit)
compose-up:
    docker compose -f deploy/compose/docker-compose.yml up -d

# Stop and remove local Docker Compose stack
compose-down:
    docker compose -f deploy/compose/docker-compose.yml down -v

# Tail logs of local Docker Compose stack
compose-logs service="":
    docker compose -f deploy/compose/docker-compose.yml logs -f {{service}}

# ==============================================================================
# Kubernetes & Helmfile Declarative Deployments
# ==============================================================================

# Diff Kubernetes resources against Helmfile declarative state
helmfile-diff env="local":
    helmfile --file deploy/helmfile.yaml --environment {{env}} diff

# Apply declarative Helmfile deployment to cluster
helmfile-apply env="local":
    helmfile --file deploy/helmfile.yaml --environment {{env}} apply

# Destroy deployed Helmfile releases
helmfile-destroy env="local":
    helmfile --file deploy/helmfile.yaml --environment {{env}} destroy

# Lint Helm charts
helm-lint:
    helm lint deploy/charts/ckodex-aiops

# ==============================================================================
# Dagger SSDLC CI/CD Harness
# ==============================================================================

# Run complete Dagger SSDLC pipeline locally (Lint, Test, Syft, Grype, Gitleaks, Build)
dagger-ci:
    dagger call -m ./ci all --source .

# Run Dagger hermetic linter step
dagger-lint:
    dagger call -m ./ci lint --source .

# Run Dagger vulnerability and SBOM scan
dagger-scan:
    dagger call -m ./ci scan-vulnerabilities --source .

# ==============================================================================
# Living Documentation (Hugo Extended)
# ==============================================================================

# Build static Hugo architecture documentation site
docs-build:
    hugo --source docs --cleanDestinationDir

# Serve Hugo living documentation site locally
docs-serve:
    hugo server --source docs -D

# ==============================================================================
# Cleanup
# ==============================================================================

# Clean temporary build artifacts, caches, and test runs
clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ data/02_intermediate/_bench.lance docs/public
