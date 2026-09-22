"""
Pytest configuration and shared fixtures for CKODEX AIOps Platform.
"""

import os
import shutil
import tempfile

# Prevent Ray from attempting to package working_dir into zip or recreate venvs on test workers
os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"
os.environ["RAY_ADDRESS"] = ""
try:
    import ray._private.ray_constants as _ray_constants

    _ray_constants.RAY_ENABLE_UV_RUN_RUNTIME_ENV = False
except Exception:
    pass
from pathlib import Path

# Ensure Kedro local configuration directory exists in all test environments
Path("conf/local").mkdir(parents=True, exist_ok=True)

import numpy as np
import polars as pl
import pytest

from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease, IntentEnvelope


@pytest.fixture
def sample_authority():
    return AuthorityPath(
        tenant="cfyd", workspace="aiops", environment="test", project="ckodex-aiops"
    )


@pytest.fixture
def sample_lease():
    return CapabilityLease(
        granted_to="principal:test-runner",
        capabilities=("pipeline:read", "pipeline:execute", "dataset:write"),
    )


@pytest.fixture
def sample_intent(sample_authority, sample_lease):
    return IntentEnvelope(
        actor="principal:tester",
        authority=sample_authority,
        requested_capability="pipeline:execute",
        lease=sample_lease,
    )


@pytest.fixture
def sample_dataframe():
    np.random.seed(42)
    n = 100
    return pl.DataFrame(
        {
            "id": [f"rec_{i:04d}" for i in range(n)],
            "timestamp_epoch": [1700000000.0 + i for i in range(n)],
            "feature_a": np.random.randn(n).tolist(),
            "feature_b": np.random.exponential(size=n).tolist(),
            "feature_c": np.random.uniform(size=n).tolist(),
            "feature_d": np.random.standard_normal(size=n).tolist(),
            "category": ["compute"] * (n // 2) + ["storage"] * (n // 2),
            "target_class": [i % 4 for i in range(n)],
        }
    )


@pytest.fixture
def temp_workspace():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)
