---
title: "Manage Configuration and Candidate Profiles"
description: "How to inspect, validate, diff, and scaffold configuration profiles using the ckx config CLI suite."
weight: 15
---

# Manage Configuration and Candidate Profiles

The `ckx-ai-project-template` provides a unified `ckx config` command group to inspect effective configurations, validate parameters against schemas and data catalogs, compare differences between profiles, and export JSON schemas for IDE autocompletion.

---

## 1. Inspect Effective Configuration

To display the resolved parameters after applying defaults, base YAML, active profile overlays, and environment variables:

### Tree View (Default)
```bash
uv run ckodex-aiops config show
```
This renders a Rich visual tree grouped by subsystem (e.g. `data_ingestion`, `model_training`, `governance`) with cryptographic digest.

### Scoped Subsystem View
```bash
uv run ckodex-aiops config show --section model_training
```

### Raw YAML or JSON Output
```bash
# Output clean YAML for scripting or piping
uv run ckodex-aiops config show --format yaml

# Output JSON with metadata
uv run ckodex-aiops config show --format json
```

### Inspect with a Candidate Profile Overlay
```bash
uv run ckodex-aiops config show --profile edge-jetson
```

---

## 2. Validate Parameters & Preflight Data Catalog

Validation checks:
- Model field constraints (e.g. `dropout_rate` between 0.0 and 1.0, learning rate > 0).
- Dimension consistency (e.g. `model_architecture.input_dim` must match length of `feature_engineering.input_features`).
- Data catalog preflight (e.g. verifying input datasets defined in `conf/base/catalog.yml` exist on disk).

```bash
uv run ckodex-aiops config validate
```

If dataset paths in the catalog do not exist yet on disk, a structured warning will identify missing artifacts without breaking offline config parsing:

```text
Validation Summary:
  Parameters: VALID
  Dimension Alignment: VALID (input_dim=4 matches 4 input_features)
  Catalog Datasets: 2 found, 2 pending generation
```

---

## 3. Compare Configuration Diffs Between Profiles

To inspect how a target candidate profile (e.g. `edge-jetson`, `workstation-dgx`, or `cluster-ray`) alters baseline parameters:

```bash
uv run ckodex-aiops config diff edge-jetson
```

This renders a formatted table showing:
- Parameter path (`section.key`)
- Baseline value
- Candidate value
- Action status (`CHANGED`, `ADDED`, `REMOVED`)

---

## 4. Scaffold Local Developer Overrides

To generate an annotated `conf/local/parameters.yml` file with smart defaults:

```bash
uv run ckodex-aiops config init
```

By default, if `conf/local/parameters.yml` already exists, `config init` will refuse to overwrite it unless `--force` is passed:

```bash
uv run ckodex-aiops config init --force
```

---

## 5. Export JSON Schema for IDE Autocompletion

To regenerate the Draft 2020-12 JSON Schema for IDE tooling and linting:

```bash
uv run ckodex-aiops config schema --out conf/parameters.schema.json
```
