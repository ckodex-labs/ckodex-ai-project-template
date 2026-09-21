"""
Unit and Conformance Tests for Platform Configuration & CLI (Rules #6, #8, #41).
Verifies Pydantic v2 schemas, candidate profile overlays, environment overrides,
catalog validation, configuration diffing, and CLI commands.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ckodex_aiops.cli import app
from ckodex_aiops.kernel.config import (
    PlatformConfig,
)

runner = CliRunner()


def test_default_platform_config() -> None:
    """Verify default instantiation of PlatformConfig and deterministic digest."""
    cfg = PlatformConfig()
    assert cfg.project.name == "ckx-ai-project-template"
    assert cfg.project.version == "0.2.0"
    assert cfg.data_ingestion.num_records > 0
    assert cfg.model.checkpoint_format == "safetensors"
    digest = cfg.compute_digest()
    assert len(digest) == 64
    assert digest == cfg.compute_digest()


def test_load_from_base_parameters() -> None:
    """Verify loading from conf/base/parameters.yml."""
    cfg = PlatformConfig.load(path=Path("conf/base/parameters.yml"), resolve_env=False)
    assert cfg.data_ingestion.num_records == 500
    assert cfg.model_training.epochs == 3
    assert cfg.feature_engineering.embedding_dim == 32
    assert cfg.sources.get("data_ingestion") == "conf/base/parameters.yml"
    # Invariant: feature embedding dim matches model input dim
    assert cfg.feature_engineering.embedding_dim == cfg.model.input_dim


def test_profile_overlay() -> None:
    """Verify candidate profile parameter and accelerator overlay."""
    cfg_metal = PlatformConfig.load(profile="macos_metal_safetensors", resolve_env=False)
    assert cfg_metal.active_profile == "macos_metal_safetensors"
    assert cfg_metal.model.device == "mps"
    assert cfg_metal.sources.get("model.device") == "profile:macos_metal_safetensors"

    cfg_cuda = PlatformConfig.load(profile="cuda_distributed_pretraining", resolve_env=False)
    assert cfg_cuda.active_profile == "cuda_distributed_pretraining"
    assert cfg_cuda.model.device == "cuda"
    assert cfg_cuda.feature_engineering.batch_size == 256
    assert cfg_cuda.feature_engineering.num_ray_actors == 4


def test_environment_variable_override(monkeypatch) -> None:
    """Verify environment variables with CKX_ prefix override values and record origin."""
    monkeypatch.setenv("CKX_MODEL_TRAINING__EPOCHS", "42")
    monkeypatch.setenv("CKX_ENVIRONMENT", "staging")
    monkeypatch.setenv("CKX_DATA_INGESTION__NUM_RECORDS", "999")

    cfg = PlatformConfig.load(resolve_env=True)
    assert cfg.model_training.epochs == 42
    assert cfg.project.environment == "staging"
    assert cfg.data_ingestion.num_records == 999
    assert cfg.sources.get("model_training") == "env:CKX_MODEL_TRAINING"


def test_configuration_diff() -> None:
    """Verify granular diffing between two configuration instances."""
    cfg_base = PlatformConfig.load(resolve_env=False)
    cfg_cuda = PlatformConfig.load(profile="cuda_distributed_pretraining", resolve_env=False)

    diffs = cfg_base.diff(cfg_cuda)
    assert len(diffs) > 0

    modified_paths = {d.path: d for d in diffs if d.status == "MODIFIED"}
    assert "model.device" in modified_paths
    assert modified_paths["model.device"].value_a == "auto"
    assert modified_paths["model.device"].value_b == "cuda"
    assert modified_paths["feature_engineering.num_ray_actors"].value_b == 4


def test_catalog_validation() -> None:
    """Verify data catalog preflight checks."""
    cfg = PlatformConfig.load(resolve_env=False)
    results = cfg.validate_catalog()

    assert len(results) >= 3
    dataset_names = [r["dataset"] for r in results]
    assert "admitted_telemetry_lance" in dataset_names
    assert "features_lance" in dataset_names
    assert "predictions_lance" in dataset_names

    for r in results:
        assert r["status"] == "PASS"


def test_json_schema_export() -> None:
    """Verify OpenAPI / JSON Schema generation."""
    schema = PlatformConfig.json_schema()
    assert schema["title"] == "PlatformConfig"
    assert "properties" in schema
    assert "data_ingestion" in schema["properties"]
    assert "governance" in schema["properties"]
    assert "telemetry" in schema["properties"]


def test_cli_config_show() -> None:
    """Verify 'ckx config show' CLI output."""
    res = runner.invoke(app, ["config", "show"])
    assert res.exit_code == 0
    assert "PlatformConfig" in res.output
    assert "data_ingestion" in res.output

    # JSON format
    res_json = runner.invoke(app, ["config", "show", "--format", "json"])
    assert res_json.exit_code == 0
    parsed = json.loads(res_json.output)
    assert parsed["project"]["name"] == "ckx-ai-project-template"

    # Profile overlay
    res_prof = runner.invoke(app, ["config", "show", "--profile", "macos_metal_safetensors"])
    assert res_prof.exit_code == 0
    assert "macos_metal_safetensors" in res_prof.output


def test_cli_config_validate() -> None:
    """Verify 'ckx config validate' CLI command."""
    res = runner.invoke(app, ["config", "validate"])
    assert res.exit_code == 0
    assert "All configuration schemas and catalog invariants validated successfully" in res.output


def test_cli_config_diff() -> None:
    """Verify 'ckx config diff' CLI command."""
    res = runner.invoke(
        app,
        [
            "config",
            "diff",
            "--profile-a",
            "macos_metal_safetensors",
            "--profile-b",
            "cuda_distributed_pretraining",
        ],
    )
    assert res.exit_code == 0
    assert "Configuration Discrepancies" in res.output
    assert "model.device" in res.output


def test_cli_config_schema(tmp_path: Path) -> None:
    """Verify 'ckx config schema' CLI command."""
    out_file = tmp_path / "schema.json"
    res = runner.invoke(app, ["config", "schema", "--output", str(out_file)])
    assert res.exit_code == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["title"] == "PlatformConfig"


def test_cli_config_init(tmp_path: Path) -> None:
    """Verify 'ckx config init' CLI command."""
    out_file = tmp_path / "test_init.yml"
    res = runner.invoke(
        app,
        ["config", "init", "--profile", "physical_ai_robotics", "--output", str(out_file)],
    )
    assert res.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "physical_ai_robotics" in content
    assert "data_ingestion:" in content


def test_cli_version_banner() -> None:
    """Verify 'ckx --version' displays platform ASCII banner."""
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "High-Assurance AI Engineering Platform" in res.output
    assert "ckx-ai-project-template v0.2.0" in res.output
