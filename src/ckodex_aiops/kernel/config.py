"""
Typed Configuration Engine for CKODEX AI Platform (CKODEX Rule #6, #8, #41).
Provides strongly typed, hierarchical, schema-validated configuration with
environment variable interpolation, candidate profile overlays, catalog validation,
and deterministic configuration diffing.
Zero external runtime infrastructure dependencies — pure semantic kernel compliant.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from ckodex_aiops.kernel.profiles import ProfileRegistry
from ckodex_aiops.kernel.receipt import compute_sha256


class ProjectMetaConfig(BaseModel):
    """Metadata describing project identity, tenant authority, and environment."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(
        default="ckx-ai-project-template",
        description="Canonical project template name",
    )
    version: str = Field(
        default="0.2.0",
        description="Semantic version of project",
    )
    environment: str = Field(
        default="development",
        description="Execution environment: development, staging, production, airgap",
    )
    tenant: str = Field(
        default="root-fabric",
        description="CKODEX standing-authority root tenant",
    )
    workspace: str = Field(
        default="default",
        description="Workspace scope identifier",
    )


class DataIngestionConfig(BaseModel):
    """Parameters for synthetic or external data ingestion pipeline."""

    model_config = ConfigDict(extra="ignore")

    num_records: int = Field(
        default=500,
        gt=0,
        description="Number of synthetic/ingested telemetry records to generate",
    )
    min_rows: int = Field(
        default=50,
        gt=0,
        description="Minimum acceptable rows for raw telemetry admission",
    )


class FeatureEngineeringConfig(BaseModel):
    """Parameters for vector feature engineering and distributed Ray execution."""

    model_config = ConfigDict(extra="ignore")

    embedding_dim: int = Field(
        default=32,
        gt=0,
        description="Dimensionality of feature embedding vectors",
    )
    num_ray_actors: int = Field(
        default=2,
        gt=0,
        description="Ray actor pool concurrency for distributed feature processing",
    )
    batch_size: int = Field(
        default=128,
        gt=0,
        description="Batch size for vector transformation streaming",
    )


class ModelArchitectureConfig(BaseModel):
    """PyTorch model architecture hyperparameters and artifact formats."""

    model_config = ConfigDict(extra="ignore")

    input_dim: int = Field(
        default=32,
        gt=0,
        description="Model input layer dimension",
    )
    hidden_dim: int = Field(
        default=64,
        gt=0,
        description="Hidden layer dimension",
    )
    num_classes: int = Field(
        default=4,
        gt=0,
        description="Number of classification target classes",
    )
    checkpoint_dir: str = Field(
        default="data/06_models",
        description="Directory for model weights and safetensors checkpoints",
    )
    device: str = Field(
        default="auto",
        description="Compute device target: auto, cpu, cuda, mps",
    )
    checkpoint_format: str = Field(
        default="safetensors",
        description="Serialization format: safetensors, pt",
    )


class ModelTrainingConfig(BaseModel):
    """Supervised training hyperparameters."""

    model_config = ConfigDict(extra="ignore")

    epochs: int = Field(
        default=3,
        gt=0,
        description="Number of training epochs",
    )
    batch_size: int = Field(
        default=32,
        gt=0,
        description="Training mini-batch size",
    )
    learning_rate: float = Field(
        default=0.001,
        gt=0.0,
        description="Optimizer learning rate",
    )


class ModelEvaluationConfig(BaseModel):
    """Evaluation criteria and quality gates."""

    model_config = ConfigDict(extra="ignore")

    min_accuracy_threshold: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Minimum accuracy threshold required for model admission",
    )


class InferenceConfig(BaseModel):
    """Batch and stream inference configuration."""

    model_config = ConfigDict(extra="ignore")

    num_ray_actors: int = Field(
        default=2,
        gt=0,
        description="Ray actor concurrency for distributed batch inference",
    )
    batch_size: int = Field(
        default=128,
        gt=0,
        description="Batch size for inference throughput",
    )


class PhysicalAIConfig(BaseModel):
    """Physical AI robotics simulation and Lance vector mining parameters."""

    model_config = ConfigDict(extra="ignore")

    num_episodes: int = Field(
        default=20,
        gt=0,
        description="Number of robotics simulation episodes",
    )
    steps_per_episode: int = Field(
        default=100,
        gt=0,
        description="Timesteps per robotics episode (100 Hz rate)",
    )
    embedding_dim: int = Field(
        default=32,
        gt=0,
        description="Multimodal robotics feature embedding dimension",
    )
    rolling_window_size: int = Field(
        default=5,
        gt=0,
        description="Rolling window size for kinematics features",
    )
    target_path: str = Field(
        default="data/04_feature/physical_ai.lance",
        description="Target Lance dataset destination for physical AI episodes",
    )
    mining_filter: str = Field(
        default="slip_detected = true",
        description="Pushdown SQL filter for Lance zero-copy mining",
    )
    mining_limit: int = Field(
        default=10,
        gt=0,
        description="Maximum mined candidate sequences to return",
    )


class RayClusterConfig(BaseModel):
    """Distributed Ray cluster execution parameters."""

    model_config = ConfigDict(extra="ignore")

    address: str | None = Field(
        default=None,
        description="Ray cluster head address (None for auto/local cluster)",
    )
    num_cpus: int | None = Field(
        default=None,
        description="Number of CPUs allocated to local Ray cluster",
    )
    num_gpus: int | None = Field(
        default=None,
        description="Number of GPUs allocated to local Ray cluster",
    )
    include_dashboard: bool = Field(
        default=False,
        description="Whether to launch Ray Web UI dashboard",
    )


class GovernanceConfig(BaseModel):
    """CKODEX Standing Authority & Governance controls (Rules #2, #8, #25, #32)."""

    model_config = ConfigDict(extra="ignore")

    authority_root: str = Field(
        default="Root Fabric",
        description="Standing authority root namespace",
    )
    strict_leases: bool = Field(
        default=True,
        description="Enforce cryptographic capability lease admission before pipeline execution",
    )
    require_receipts: bool = Field(
        default=True,
        description="Enforce Merkle lineage and evidence receipt generation on dataset saves",
    )
    auto_quarantine_on_violation: bool = Field(
        default=True,
        description="Automatically isolate non-conformant or drifted datasets to quarantine",
    )


class TelemetryConfig(BaseModel):
    """Observability, OpenTelemetry, and Four Truth Channels (Rules #12, #38)."""

    model_config = ConfigDict(extra="ignore")

    service_name: str = Field(
        default="ckx-ai-project-template",
        description="OpenTelemetry service name identifier",
    )
    export_otlp: bool = Field(
        default=False,
        description="Export traces and metrics via gRPC OTLP collector",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
    )
    truth_channels_enabled: bool = Field(
        default=True,
        description="Enable Four Truth Channels correlation (Telemetry, Execution, Decision, Evidence)",
    )


@dataclass
class ConfigDiffEntry:
    """Represents a discrete difference between two configuration states."""

    path: str
    value_a: Any
    value_b: Any
    status: str  # IDENTICAL, MODIFIED, ADDED, REMOVED


class PlatformConfig(BaseModel):
    """
    Unified Platform Configuration for CKODEX AI Platform.
    Integrates Kedro parameters, active candidate profiles, environment overrides,
    and governance invariants.
    """

    model_config = ConfigDict(extra="ignore")

    project: ProjectMetaConfig = Field(default_factory=ProjectMetaConfig)
    data_ingestion: DataIngestionConfig = Field(default_factory=DataIngestionConfig)
    feature_engineering: FeatureEngineeringConfig = Field(default_factory=FeatureEngineeringConfig)
    model: ModelArchitectureConfig = Field(default_factory=ModelArchitectureConfig)
    model_training: ModelTrainingConfig = Field(default_factory=ModelTrainingConfig)
    model_evaluation: ModelEvaluationConfig = Field(default_factory=ModelEvaluationConfig)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    physical_ai: PhysicalAIConfig = Field(default_factory=PhysicalAIConfig)
    ray: RayClusterConfig = Field(default_factory=RayClusterConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)

    active_profile: str | None = Field(
        default=None,
        description="Name of currently active platform profile or baseline",
    )
    sources: dict[str, str] = Field(
        default_factory=dict,
        description="Provenance map recording the origin of each configuration section",
    )

    def compute_digest(self) -> str:
        """Computes deterministic SHA-256 digest of this configuration state."""
        dumped = json.dumps(self.model_dump(exclude={"sources"}), sort_keys=True)
        return compute_sha256(dumped.encode("utf-8"))

    @classmethod
    def load(
        cls,
        path: Path | str | None = None,
        profile: str | None = None,
        resolve_env: bool = True,
    ) -> PlatformConfig:
        """
        Loads and validates platform configuration from YAML files, active profile, and environment.

        Resolution precedence (lowest to highest):
        1. Built-in Pydantic Defaults
        2. Base YAML (`conf/base/parameters.yml` or custom path)
        3. Local YAML (`conf/local/parameters.yml` if present)
        4. Platform Profile (e.g. `macos_metal_safetensors`)
        5. Environment Variables (`CKX_*` prefix)
        """
        raw_config: dict[str, Any] = {}
        sources: dict[str, str] = {}

        # 1. Base parameters YAML
        base_path = Path(path) if path else Path("conf/base/parameters.yml")
        if base_path.is_file():
            try:
                with open(base_path, encoding="utf-8") as f:
                    loaded = yaml.safe_load(f)
                    if isinstance(loaded, dict):
                        raw_config = _deep_merge(raw_config, loaded)
                        for k in loaded:
                            sources[k] = str(base_path)
            except Exception as e:
                raise ValueError(f"Failed to parse base parameters YAML at {base_path}: {e}") from e

        # 2. Local parameters YAML override
        local_path = Path("conf/local/parameters.yml")
        if not path and local_path.is_file():
            try:
                with open(local_path, encoding="utf-8") as f:
                    local_loaded = yaml.safe_load(f)
                    if isinstance(local_loaded, dict):
                        raw_config = _deep_merge(raw_config, local_loaded)
                        for k in local_loaded:
                            sources[k] = str(local_path)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse local parameters YAML at {local_path}: {e}"
                ) from e

        # 3. Candidate profile overlay
        active_prof = profile or os.getenv("CKX_PROFILE")
        if active_prof:
            try:
                prof = ProfileRegistry.get(active_prof)
                # Merge profile-declared parameters
                raw_config = _deep_merge(raw_config, prof.parameters)
                for k in prof.parameters:
                    sources[k] = f"profile:{prof.name}"

                # Overlay device & checkpoint format into model section
                if "model" not in raw_config:
                    raw_config["model"] = {}
                if prof.device != "auto":
                    raw_config["model"]["device"] = prof.device
                if prof.checkpoint_format:
                    raw_config["model"]["checkpoint_format"] = prof.checkpoint_format
                sources["model.device"] = f"profile:{prof.name}"
            except KeyError as e:
                raise ValueError(f"Unknown profile '{active_prof}': {e}") from e

        # 4. Environment variable overrides (CKX_ prefix)
        if resolve_env:
            env_overrides = _parse_env_overrides()
            if env_overrides:
                raw_config = _deep_merge(raw_config, env_overrides)
                for section in env_overrides:
                    sources[section] = f"env:CKX_{section.upper()}"

        # 5. Instantiate and validate
        config = cls.model_validate(raw_config)
        config.active_profile = active_prof
        config.sources = sources
        return config

    def validate_catalog(self, catalog_path: Path | str | None = None) -> list[dict[str, Any]]:
        """
        Validates the Kedro data catalog datasets against configuration expectations and filesystem constraints.
        Returns a list of check results with status, dataset, and diagnostic messages.
        """
        cat_path = Path(catalog_path) if catalog_path else Path("conf/base/catalog.yml")
        results: list[dict[str, Any]] = []

        if not cat_path.is_file():
            results.append(
                {
                    "dataset": "catalog_file",
                    "status": "FAIL",
                    "message": f"Catalog file not found: {cat_path}",
                }
            )
            return results

        try:
            with open(cat_path, encoding="utf-8") as f:
                catalog_data = yaml.safe_load(f)
        except Exception as e:
            results.append(
                {
                    "dataset": "catalog_syntax",
                    "status": "FAIL",
                    "message": f"Failed to parse catalog YAML: {e}",
                }
            )
            return results

        if not isinstance(catalog_data, dict):
            results.append(
                {
                    "dataset": "catalog_structure",
                    "status": "FAIL",
                    "message": "Catalog YAML root must be a dictionary of datasets",
                }
            )
            return results

        for ds_name, ds_spec in catalog_data.items():
            if not isinstance(ds_spec, dict):
                results.append(
                    {
                        "dataset": ds_name,
                        "status": "FAIL",
                        "message": "Dataset entry must be a dictionary specification",
                    }
                )
                continue

            ds_type = ds_spec.get("type", "unknown")
            filepath = ds_spec.get("filepath")

            if not filepath:
                results.append(
                    {
                        "dataset": ds_name,
                        "status": "FAIL",
                        "message": "Missing 'filepath' parameter in catalog specification",
                    }
                )
                continue

            target_path = Path(filepath)
            parent_dir = target_path.parent

            # Check parent directory accessibility
            if not parent_dir.exists():
                results.append(
                    {
                        "dataset": ds_name,
                        "status": "PASS",
                        "message": f"Parent directory {parent_dir} will be auto-created on pipeline execution (type: {ds_type})",
                    }
                )
            else:
                results.append(
                    {
                        "dataset": ds_name,
                        "status": "PASS",
                        "message": f"Target path {filepath} validated (type: {ds_type})",
                    }
                )

        return results

    def diff(self, other: PlatformConfig) -> list[ConfigDiffEntry]:
        """
        Computes granular differences between self and another PlatformConfig.
        """
        dict_a = self.model_dump(exclude={"sources"})
        dict_b = other.model_dump(exclude={"sources"})

        diffs: list[ConfigDiffEntry] = []
        _compare_dicts("", dict_a, dict_b, diffs)
        return diffs

    def to_yaml(self) -> str:
        """Serializes current configuration to clean, human-readable YAML."""
        data = self.model_dump(exclude={"sources"})
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def to_json(self, indent: int = 2) -> str:
        """Serializes configuration to formatted JSON."""
        return self.model_dump_json(indent=indent, exclude={"sources"})

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """Returns JSON Schema for the platform configuration model."""
        return cls.model_json_schema()


def _deep_merge(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Recursively merges dict2 into dict1 without mutating inputs."""
    result = dict(dict1)
    for k, v in dict2.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _parse_env_overrides() -> dict[str, Any]:
    """
    Parses environment variables prefixed with CKX_ into a nested dictionary.
    Convention: CKX_<SECTION>__<KEY>=<VALUE>
    Example: CKX_MODEL_TRAINING__EPOCHS=5 -> {"model_training": {"epochs": 5}}
             CKX_ENVIRONMENT=staging -> {"project": {"environment": "staging"}}
    """
    result: dict[str, Any] = {}
    for key, val in os.environ.items():
        if not key.startswith("CKX_"):
            continue

        raw_key = key[4:].lower()

        # Handle top-level shortcuts
        if raw_key in ("environment", "tenant", "workspace"):
            if "project" not in result:
                result["project"] = {}
            result["project"][raw_key] = _cast_env_val(val)
            continue

        if "__" in raw_key:
            section, subkey = raw_key.split("__", 1)
            if section not in result:
                result[section] = {}
            result[section][subkey] = _cast_env_val(val)
        else:
            result[raw_key] = _cast_env_val(val)

    return result


def _cast_env_val(val: str) -> Any:
    """Attempts smart scalar casting for environment variable strings."""
    if val.lower() in ("true", "yes", "1"):
        return True
    if val.lower() in ("false", "no", "0"):
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def _compare_dicts(
    prefix: str,
    a: dict[str, Any],
    b: dict[str, Any],
    diffs: list[ConfigDiffEntry],
) -> None:
    """Helper to compute recursive differences between two dictionaries."""
    all_keys = sorted(set(a.keys()) | set(b.keys()))
    for k in all_keys:
        curr_path = f"{prefix}.{k}" if prefix else k
        if k not in a:
            diffs.append(
                ConfigDiffEntry(
                    path=curr_path,
                    value_a=None,
                    value_b=b[k],
                    status="ADDED",
                )
            )
        elif k not in b:
            diffs.append(
                ConfigDiffEntry(
                    path=curr_path,
                    value_a=a[k],
                    value_b=None,
                    status="REMOVED",
                )
            )
        else:
            val_a = a[k]
            val_b = b[k]
            if isinstance(val_a, dict) and isinstance(val_b, dict):
                _compare_dicts(curr_path, val_a, val_b, diffs)
            elif val_a != val_b:
                diffs.append(
                    ConfigDiffEntry(
                        path=curr_path,
                        value_a=val_a,
                        value_b=val_b,
                        status="MODIFIED",
                    )
                )
            else:
                diffs.append(
                    ConfigDiffEntry(
                        path=curr_path,
                        value_a=val_a,
                        value_b=val_b,
                        status="IDENTICAL",
                    )
                )
