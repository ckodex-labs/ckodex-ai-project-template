---
title: "Configuration Reference (PlatformConfig)"
description: "Authoritative specification for the CKODEX typed configuration engine, parameters schema, environment overrides, and profile overlays."
weight: 15
---

# Configuration Reference (`PlatformConfig`)

The `ckx-ai-project-template` runtime employs a strongly typed, hierarchical, schema-validated configuration system powered by Pydantic v2 and PyYAML.

All configuration originates from declarative parameter specifications, supports candidate profile overlays, environment variable overrides (`CKX_*`), and provides preflight validation against dataset catalogs.

---

## 1. Hierarchy and Merging Precedence

The effective configuration is computed using a deterministic deep-merge cascade:

```
Default Field Values (Pydantic Models)
      │
      ▼
Base Parameters (conf/base/parameters.yml)
      │
      ▼
Profile Overlays (from ProfileRegistry, e.g. edge-jetson, cluster-ray)
      │
      ▼
Local Parameters (conf/local/parameters.yml)
      │
      ▼
Environment Overrides (CKX_* variables)
      │
      ▼
Runtime Parameters (Programmatic overrides)
```

1. **Default Values**: Built-in conservative defaults ensuring zero-config local operation.
2. **`conf/base/parameters.yml`**: Project-wide baseline settings committed to version control.
3. **Profile Overlays**: Hardware-specific configurations loaded from the canonical profile registry (e.g. `edge-jetson`, `workstation-dgx`, `cluster-ray`).
4. **`conf/local/parameters.yml`**: Environment-specific overrides (gitignored, developer/node local).
5. **Environment Overrides**: Flat or nested environment variables prefixed with `CKX_`. Nested dictionaries are delimited by double underscores `__` (e.g. `CKX_MODEL_TRAINING__BATCH_SIZE=64`).
6. **Programmatic Runtime Parameters**: Explicit dictionaries passed to `PlatformConfig.load(runtime_params=...)`.

---

## 2. Configuration Subsystems

`PlatformConfig` is composed of 11 domain-specific Pydantic models:

### 2.1 Project Metadata (`project`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` | `"ckx-ai-project-template"` | Canonical name of the project. |
| `version` | `str` | `"0.1.0"` | SemVer release version. |
| `tenant` | `str` | `"ckodex-labs"` | Authority hierarchy tenant. |
| `workspace` | `str` | `"aiops-dev"` | Active workspace namespace. |
| `environment` | `str` | `"development"` | Target environment (`development`, `staging`, `production`). |

### 2.2 Data Ingestion (`data_ingestion`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `raw_data_dir` | `str` | `"data/01_raw"` | Directory holding raw ingested artifacts. |
| `batch_size` | `int` | `1000` | Ingestion streaming batch size. |
| `supported_formats` | `List[str]` | `["parquet", "lance", "json", "csv"]` | Allowed data file extensions. |
| `checksum_algorithm` | `str` | `"sha256"` | Hash algorithm for content-addressable storage. |

### 2.3 Feature Engineering (`feature_engineering`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `input_features` | `List[str]` | `["dim_0", "dim_1", "dim_2", "dim_3"]` | Feature column identifiers. |
| `label_column` | `str` | `"target"` | Target label column name. |
| `normalize` | `bool` | `True` | Whether to apply standard feature normalization. |
| `train_split` | `float` | `0.8` | Ratio of data allocated to training partition. |
| `validation_split` | `float` | `0.1` | Ratio of data allocated to validation partition. |
| `test_split` | `float` | `0.1` | Ratio of data allocated to testing partition. |

### 2.4 Model Architecture (`model_architecture`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `architecture_name` | `str` | `"mlp"` | Model family identifier (`mlp`, `resnet`, `transformer`, `robotics_policy`). |
| `input_dim` | `int` | `4` | Input dimension count (must match `input_features`). |
| `hidden_dim` | `int` | `128` | Hidden layer dimension width. |
| `num_hidden_layers` | `int` | `2` | Count of hidden layer blocks. |
| `output_dim` | `int` | `1` | Model output tensor dimension. |
| `dropout_rate` | `float` | `0.1` | Dropout regularization probability (0.0 to 1.0). |

### 2.5 Model Training (`model_training`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `epochs` | `int` | `10` | Total training iterations over dataset. |
| `learning_rate` | `float` | `0.001` | Initial optimizer learning rate. |
| `batch_size` | `int` | `32` | Training mini-batch size. |
| `weight_decay` | `float` | `0.0001` | L2 weight regularization factor. |
| `checkpoint_interval` | `int` | `5` | Checkpointing frequency in epochs. |
| `early_stopping_patience` | `int` | `3` | Epochs without improvement before early termination. |

### 2.6 Model Evaluation (`model_evaluation`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `metrics` | `List[str]` | `["mse", "mae", "r2"]` | Evaluation metrics computed on test set. |
| `target_threshold` | `float` | `0.05` | Maximum allowable MSE error for model admission. |
| `drift_baseline_path` | `Optional[str]` | `None` | Path to baseline dataset for Wasserstein drift comparison. |

### 2.7 Inference & Serving (`inference`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `host` | `str` | `"0.0.0.0"` | HTTP Gateway bind interface. |
| `port` | `int` | `8080` | HTTP Gateway listen port. |
| `workers` | `int` | `1` | Serving worker concurrency. |
| `max_batch_latency_ms` | `int` | `50` | Dynamic batching timeout threshold. |
| `quantize_mode` | `Optional[str]` | `None` | Quantization mode (`int8`, `fp16`, or null). |

### 2.8 Physical AI & Robotics (`physical_ai`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enabled` | `bool` | `False` | Enable robotics telemetry and real-time control plane. |
| `control_frequency_hz` | `int` | `50` | Actuator feedback loop target frequency. |
| `safety_interlock` | `bool` | `True` | Hardware kill-switch interlock requirement. |
| `telemetry_buffer_size` | `int` | `10000` | In-memory ring buffer capacity for kinematic logs. |

### 2.9 Ray Cluster (`ray_cluster`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `address` | `Optional[str]` | `None` | Ray head node address (auto/local if null). |
| `num_cpus` | `Optional[int]` | `None` | CPU core budget allocation. |
| `num_gpus` | `Optional[int]` | `None` | GPU accelerator count allocation. |
| `object_store_memory_mb` | `Optional[int]` | `None` | Plasma shared-memory store budget in MB. |

### 2.10 Governance & Compliance (`governance`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `require_attestations` | `bool` | `True` | Enforce SLSA In-toto cryptographic attestations. |
| `require_sbom` | `bool` | `True` | Enforce CycloneDX / SPDX SBOM presence. |
| `airgap_mode` | `bool` | `False` | Disallow all outbound internet egress during runs. |
| `allow_derogations` | `bool` | `False` | Permit authorized technical risk derogations. |
| `oscal_catalog_path` | `str` | `"docs/oscal/nist_sp_800_53.json"` | Path to NIST OSCAL security controls definition. |

### 2.11 Telemetry & Observability (`telemetry`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `service_name` | `str` | `"ckx-aiops"` | OpenTelemetry resource service name. |
| `otlp_endpoint` | `Optional[str]` | `None` | OTLP gRPC/HTTP exporter collector endpoint. |
| `flight_recorder_enabled` | `bool` | `True` | Record ring-buffer receipts for post-mortem analysis. |
| `sample_rate` | `float` | `1.0` | Trace sampling probability (0.0 to 1.0). |

---

## 3. Environment Variable Overrides

Any configuration value can be overridden via environment variables without editing YAML files:

```bash
# Override project metadata
export CKX_PROJECT__ENVIRONMENT="production"

# Override model training hyperparameters
export CKX_MODEL_TRAINING__BATCH_SIZE=64
export CKX_MODEL_TRAINING__LEARNING_RATE=0.0005

# Override governance policy
export CKX_GOVERNANCE__AIRGAP_MODE=true
export CKX_GOVERNANCE__ALLOW_DEROGATIONS=false
```

---

## 4. IDE Integration via JSON Schema

The repository maintains an authoritative Draft 2020-12 JSON Schema at `conf/parameters.schema.json`.

To enable autocomplete and real-time schema validation in Visual Studio Code or JetBrains IDEs, add the YAML header comment to your parameters file:

```yaml
# yaml-language-server: $schema=../parameters.schema.json
project:
  name: "ckx-ai-project-template"
  environment: "production"

model_training:
  epochs: 25
  batch_size: 64
```

To re-export the schema after modifying models:

```bash
uv run ckodex-aiops config schema --out conf/parameters.schema.json
```
