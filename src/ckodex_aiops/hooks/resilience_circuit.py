"""
Kedro Hook: Resilience Patterns, Circuit Breaking & Forensic Quarantine (Rules #28, #29, #31, #32).
Ensures:
1. Circuit Breakers isolate failing nodes and prevent cascading pipeline collapse.
2. Forensic Quarantine preserves evidence upon node failure without destroying diagnostic state.
3. State transitions reflect explicit degradation: NORMAL -> DEGRADED -> SAFE_HOLD -> QUARANTINED.
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any

from kedro.framework.hooks import hook_impl
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from rich.console import Console

from ckodex_aiops.kernel.quarantine import QuarantineManager
from ckodex_aiops.kernel.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)

console = Console()


class ResilienceCircuitBreakerHook:
    """
    Guards pipeline execution with per-node circuit breakers and automatic forensic quarantine.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_cooldown_seconds: float = 2.0,
        quarantine_dir: str = "data/08_reporting/quarantine",
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_cooldown_seconds = recovery_cooldown_seconds
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(self, node_name: str) -> CircuitBreaker:
        if node_name not in self._breakers:
            cfg = CircuitBreakerConfig(
                failure_threshold=self.failure_threshold,
                recovery_cooldown_seconds=self.recovery_cooldown_seconds,
                name=node_name,
            )
            self._breakers[node_name] = CircuitBreaker(cfg)
        return self._breakers[node_name]

    @hook_impl
    def before_node_run(
        self,
        node: Node,
        catalog: Any,
        inputs: dict[str, Any],
        is_async: bool,
    ) -> None:
        breaker = self.get_breaker(node.name)
        state = breaker.get_state()
        if state == CircuitState.OPEN:
            msg = (
                f"Circuit breaker for node '{node.name}' is OPEN (failure budget exhausted). "
                f"Halting node execution to contain failure propagation."
            )
            console.print(f"[bold red]✖ Circuit OPEN:[/bold red] {msg}")
            raise CircuitBreakerOpenError(msg)

    @hook_impl
    def after_node_run(
        self,
        node: Node,
        catalog: Any,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        is_async: bool,
    ) -> None:
        breaker = self.get_breaker(node.name)
        breaker.record_success()

    @hook_impl
    def on_node_error(
        self,
        error: Exception,
        node: Node,
        catalog: Any,
        inputs: dict[str, Any],
        is_async: bool,
    ) -> None:
        breaker = self.get_breaker(node.name)
        breaker.record_failure(error)

        console.print(
            f"[bold red]✖ Node '{node.name}' Failed:[/bold red] {type(error).__name__}: {error} "
            f"(Trip count: {breaker.total_trips}, State: {breaker.get_state().value})"
        )

        # Automatic Forensic Quarantine (Rule #32: Quarantine preserves evidence)
        incident_id = f"inc_{node.name}_{int(time.time())}"
        forensic_payload = {
            "incident_id": incident_id,
            "node_name": node.name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "inputs_count": len(inputs),
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "circuit_state": breaker.get_state().value,
        }

        incident_file = self.quarantine_dir / f"{incident_id}.json"
        with open(incident_file, "w", encoding="utf-8") as f:
            json.dump(forensic_payload, f, indent=2)

        qm = QuarantineManager(self.quarantine_dir)
        qm.isolate_artifact(
            target_path=incident_file,
            trigger_anomaly=f"Execution failure: {type(error).__name__}: {error}",
            target_type="INCIDENT_RECORD",
        )
        console.print(
            f"[dim red]  └─ Forensic Evidence Quarantined:[/dim red] [dim]{incident_file}[/dim]"
        )

    @hook_impl
    def on_pipeline_error(
        self,
        error: Exception,
        run_params: dict[str, Any],
        pipeline: Pipeline,
        catalog: Any,
    ) -> None:
        console.print(
            f"[bold red]✖ Pipeline Execution Halted with Failure:[/bold red] {type(error).__name__}: {error}"
        )
