"""
Tests for Resilience Patterns: Circuit Breakers, Bounded Retries & Degraded Modes.
"""

from __future__ import annotations

import time

import pytest

from ckodex_aiops.kernel.resilience import (
    BoundedRetry,
    BoundedRetryConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    DegradedContract,
    DegradedModeRegistry,
)


def test_circuit_breaker_transitions():
    cfg = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_cooldown_seconds=0.1,
        half_open_success_threshold=1,
        name="test_breaker",
    )
    cb = CircuitBreaker(cfg)

    # 1. Starts CLOSED
    assert cb.get_state() == CircuitState.CLOSED

    # 2. First failure stays CLOSED
    cb.record_failure(ValueError("flaky"))
    assert cb.get_state() == CircuitState.CLOSED

    # 3. Second failure trips to OPEN
    cb.record_failure(ValueError("deadly"))
    assert cb.get_state() == CircuitState.OPEN
    assert cb.total_trips == 1

    # 4. Executing while OPEN raises CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        cb.execute(lambda: 42)

    # 5. Fallback works while OPEN
    fallback_res = cb.execute_with_fallback(lambda: 42, lambda: 99)
    assert fallback_res == 99

    # 6. After cooldown, transitions to HALF_OPEN
    time.sleep(0.12)
    assert cb.get_state() == CircuitState.HALF_OPEN

    # 7. Success in HALF_OPEN recovers back to CLOSED
    cb.record_success()
    assert cb.get_state() == CircuitState.CLOSED


def test_bounded_retry_with_jitter():
    cfg = BoundedRetryConfig(
        max_retries=2,
        base_delay_seconds=0.01,
        max_delay_seconds=0.05,
    )

    attempts = 0

    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError(f"fail {attempts}")
        return "recovered"

    result = BoundedRetry.execute(flaky_func, config=cfg)
    assert result == "recovered"
    assert attempts == 3

    # Test failure after max retries
    def always_fails():
        raise ValueError("unrecoverable")

    with pytest.raises(ValueError, match="unrecoverable"):
        BoundedRetry.execute(always_fails, config=cfg)


def test_degraded_mode_registry():
    contract = DegradedContract(
        component_name="ray_inference",
        trigger="ray_worker_oom",
        residual_capabilities=("inference:cpu_local", "dataset:read"),
        prohibited_capabilities=("inference:gpu_cluster", "model:train"),
        data_guarantees="Deterministic float32 on CPU",
        recovery_criteria="Memory usage below 80% for 5 min",
    )
    DegradedModeRegistry.register_contract(contract)

    # In NORMAL mode, all capabilities permitted
    assert (
        DegradedModeRegistry.is_capability_permitted("ray_inference", "inference:gpu_cluster")
        is True
    )

    # Activate DEGRADED mode
    sv = DegradedModeRegistry.activate_degraded_mode("ray_inference")
    assert sv.lifecycle.value == "DEGRADED"

    # In DEGRADED mode, residual capability is allowed, prohibited is denied
    assert (
        DegradedModeRegistry.is_capability_permitted("ray_inference", "inference:cpu_local") is True
    )
    assert (
        DegradedModeRegistry.is_capability_permitted("ray_inference", "inference:gpu_cluster")
        is False
    )

    # Recover component
    sv_recovered = DegradedModeRegistry.recover_component("ray_inference")
    assert sv_recovered.lifecycle.value == "NORMAL"
    assert (
        DegradedModeRegistry.is_capability_permitted("ray_inference", "inference:gpu_cluster")
        is True
    )
