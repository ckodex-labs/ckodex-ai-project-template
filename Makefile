.PHONY: help install sync test lint format doctor run-pipeline benchmark verify mine compact clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies with UV"
	@echo "  make sync          - Sync lockfile with UV"
	@echo "  make doctor        - Run Day-2 platform preflight health checks"
	@echo "  make test          - Run pytest test suite"
	@echo "  make lint          - Run ruff linting"
	@echo "  make format        - Run ruff code formatting"
	@echo "  make run-pipeline  - Execute full Kedro end-to-end pipeline"
	@echo "  make benchmark     - Run throughput micro-benchmarks (Polars vs Lance vs Ray)"
	@echo "  make verify        - Audit and verify cryptographic lineage receipts"
	@echo "  make mine          - Run Physical AI multimodal SQL pushdown event mining"
	@echo "  make compact       - Run distributed fragment compaction on Lance dataset"
	@echo "  make clean         - Clean temporary artifacts and cache"

install:
	uv sync

sync:
	uv lock --check || uv lock

doctor:
	uv run ckodex-aiops doctor

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

run-pipeline:
	uv run ckodex-aiops run --pipeline __default__

benchmark:
	uv run ckodex-aiops benchmark

verify:
	uv run ckodex-aiops verify

mine:
	uv run ckodex-aiops mine

compact:
	uv run ckodex-aiops compact data/04_feature/physical_ai.lance

profile-list:
	uv run ckodex-aiops profile list

docs-build:
	hugo --source docs --cleanDestinationDir

docs-serve:
	hugo server --source docs -D

dagger-ci:
	dagger call -m ./ci all --source .

dagger-lint:
	dagger call -m ./ci lint --source .

dagger-scan:
	dagger call -m ./ci scan-vulnerabilities --source .

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ data/02_intermediate/_bench.lance docs/public

