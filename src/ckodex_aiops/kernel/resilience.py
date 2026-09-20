"""
Pure Semantic Kernel: Resilience Patterns, Circuit Breakers & Bounded Backoff (Rules #29, #30, #31).
Enforces:
1. Bounded failure budgets and circuit breaking (Closed -> Open -> Half-Open).
2. Bounded retries with exponential backoff and randomized full jitter.
3. Explicit degraded mode contracts with residual capability gating.
"""

from __future__ import annotations

import enum
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)

T = TypeVar("T")


class CircuitState(enum.Enum):
    CLOSED = "CLOSED"  # Normal execution, failures increment counter
    OPEN = "OPEN"  # Tripped, requests fail-fast or invoke degraded fallback
    HALF_OPEN = "HALF_OPEN"  # Testing recovery with bounded probe calls


class CircuitBreakerOpenError(RuntimeError):
    """Raised when an operation is attempted on an OPEN circuit breaker without fallback."""


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3
    recovery_cooldown_seconds: float = 2.0
    half_open_success_threshold: int = 2
    name: str = "default_breaker"


class CircuitBreaker:
    """
    High-assurance Circuit Breaker enforcing failure budgets and short-circuit containment (Rule #31).
    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.total_trips = 0

    def get_state(self) -> CircuitState:
        """Evaluates time-based state transitions from OPEN to HALF_OPEN."""
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.config.recovery_cooldown_seconds:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
        return self.state

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.half_open_success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self, exc: Exception | None = None) -> None:
        self.last_failure_time = time.time()
        self.failure_count += 1
        if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            if (
                self.failure_count >= self.config.failure_threshold
                or self.state == CircuitState.HALF_OPEN
            ):
                self.state = CircuitState.OPEN
                self.total_trips += 1

    def execute(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes the callable guarded by circuit state."""
        state = self.get_state()
        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.config.name}' is OPEN. Consequential calls are halted to contain blast radius."
            )

        try:
            result = fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure(exc)
            raise

    def execute_with_fallback(
        self,
        fn: Callable[..., T],
        fallback_fn: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Executes callable, gracefully invoking fallback if OPEN or upon failure."""
        state = self.get_state()
        if state == CircuitState.OPEN:
            return fallback_fn(*args, **kwargs)

        try:
            result = fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure(exc)
            return fallback_fn(*args, **kwargs)


@dataclass(frozen=True)
class BoundedRetryConfig:
    max_retries: int = 3
    base_delay_seconds: float = 0.05
    max_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0


class BoundedRetry:
    """
    Bounded retry policy with exponential backoff and randomized full jitter (Rule #31).
    Prevents thundering herds and unbounded retry loops.
    """

    @classmethod
    def calculate_backoff(cls, attempt: int, config: BoundedRetryConfig) -> float:
        """Computes exponential backoff with full jitter: Uniform(0, min(max_delay, base * mult^attempt))."""
        calculated = config.base_delay_seconds * (config.backoff_multiplier**attempt)
        ceiling = min(config.max_delay_seconds, calculated)
        return random.uniform(0.0, ceiling)

    @classmethod
    def execute(
        cls,
        fn: Callable[..., T],
        config: BoundedRetryConfig | None = None,
        retry_exceptions: tuple[type[Exception], ...] = (Exception,),
        *args: Any,
        **kwargs: Any,
    ) -> T:
        cfg = config or BoundedRetryConfig()
        last_exc: Exception | None = None

        for attempt in range(cfg.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except retry_exceptions as exc:
                last_exc = exc
                if attempt == cfg.max_retries:
                    break
                sleep_duration = cls.calculate_backoff(attempt, cfg)
                time.sleep(sleep_duration)

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Bounded retry failed with unspecified error.")


@dataclass(frozen=True)
class DegradedContract:
    """
    Explicit specification of a degraded operational mode (Rule #30).
    """

    component_name: str
    trigger: str
    residual_capabilities: tuple[str, ...]
    prohibited_capabilities: tuple[str, ...]
    data_guarantees: str
    recovery_criteria: str
    maximum_exposure_duration_sec: float = 3600.0


class DegradedModeRegistry:
    """
    Manages explicit platform degraded state contracts and residual capability verification.
    """

    _contracts: dict[str, DegradedContract] = {}
    _active_degradations: dict[str, float] = {}

    @classmethod
    def register_contract(cls, contract: DegradedContract) -> None:
        cls._contracts[contract.component_name] = contract

    @classmethod
    def activate_degraded_mode(cls, component_name: str) -> StateVector:
        """Transitions component into explicit degraded operational mode."""
        cls._active_degradations[component_name] = time.time()
        return StateVector(
            presence=Presence.PRESENT,
            valence=Valence.MIXED,
            anti=Anti.NONE,
            coherence=Coherence.PARTIALLY_COHERENT,
            evidence=EvidenceStatus.VERIFIED,
            lifecycle=OperationalLifecycle.DEGRADED,
        )

    @classmethod
    def recover_component(cls, component_name: str) -> StateVector:
        """Restores component to NORMAL operational mode."""
        cls._active_degradations.pop(component_name, None)
        return StateVector(
            presence=Presence.PRESENT,
            valence=Valence.POSITIVE,
            anti=Anti.NONE,
            coherence=Coherence.COHERENT,
            evidence=EvidenceStatus.VERIFIED,
            lifecycle=OperationalLifecycle.NORMAL,
        )

    @classmethod
    def is_capability_permitted(cls, component_name: str, capability: str) -> bool:
        """Verifies if capability is permitted under active degradation contract."""
        if component_name not in cls._active_degradations:
            return True  # NORMAL mode allows all declared capabilities

        contract = cls._contracts.get(component_name)
        if not contract:
            return False  # Without contract, deny all operations under active degradation

        if capability in contract.prohibited_capabilities:
            return False

        return capability in contract.residual_capabilities
