"""
Kedro Hook: Authority Admission & Capability Lease Gating (Rules #2, #4, #11, #25).
Ensures:
1. Authority Precedes Everything: Execution cannot proceed without valid IntentEnvelope.
2. Capability Leases must be active, unrevoked, unexpired, and scope-attenuated.
3. Proof Before Side Effects: Preflight gating stops unauthorized operations before mutations occur.
"""

from __future__ import annotations

import os
import time
from typing import Any

from kedro.framework.hooks import hook_impl
from kedro.pipeline.node import Node
from rich.console import Console

from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease, IntentEnvelope
from ckodex_aiops.validation.validators import AuthorityValidator

console = Console()


class AdmissionDeniedError(PermissionError):
    """Raised when an operation fails preflight authority or capability lease admission."""


class AuthorityAdmissionHook:
    """
    Guards pipeline and node execution against unauthorized or unleased execution.
    """

    def __init__(
        self,
        default_intent: IntentEnvelope | None = None,
        strict_mode: bool = True,
    ) -> None:
        self.strict_mode = strict_mode
        self._current_intent = default_intent or self._create_default_intent()

    def _create_default_intent(self) -> IntentEnvelope:
        tenant = os.environ.get("CKODEX_TENANT", "cfyd")
        workspace = os.environ.get("CKODEX_WORKSPACE", "aiops")
        env = os.environ.get("CKODEX_ENVIRONMENT", "production")
        project = os.environ.get("CKODEX_PROJECT", "ckx-ai-project-template")

        authority = AuthorityPath(
            tenant=tenant,
            workspace=workspace,
            environment=env,
            project=project,
        )
        lease = CapabilityLease(
            granted_to=f"service-account:{project}-runner",
            capabilities=(
                "pipeline:execute",
                "dataset:read",
                "dataset:write",
                "model:train",
                "model:evaluate",
                "model:serve",
            ),
            expires_at_epoch=time.time() + 7200.0,
        )
        return IntentEnvelope(
            actor=f"principal:{project}-runner",
            authority=authority,
            requested_capability="pipeline:execute",
            lease=lease,
        )

    def set_intent(self, intent: IntentEnvelope) -> None:
        self._current_intent = intent

    @hook_impl
    def before_pipeline_run(
        self,
        run_params: dict[str, Any],
        pipeline: Any,
        catalog: Any,
    ) -> None:
        console.print(
            "[bold cyan]⠹ Authority Hook:[/bold cyan] Validating standing authority and capability lease..."
        )
        outcome = AuthorityValidator.validate(self._current_intent, "pipeline:execute")

        if not outcome.admitted:
            reasons = "; ".join(outcome.violations)
            console.print(f"[bold red]✖ Admission DENIED:[/bold red] {reasons}")
            if self.strict_mode:
                raise AdmissionDeniedError(
                    f"Pipeline admission denied by AuthorityValidator: {reasons}"
                )
        else:
            console.print(
                f"[bold green]✔ Standing Authority Admitted:[/bold green] "
                f"Tenant: [cyan]{self._current_intent.authority.tenant}[/cyan] | "
                f"Workspace: [cyan]{self._current_intent.authority.workspace}[/cyan] | "
                f"Lease: [dim]{self._current_intent.lease.lease_id}[/dim]"
            )

    @hook_impl
    def before_node_run(
        self,
        node: Node,
        catalog: Any,
        inputs: dict[str, Any],
        is_async: bool,
    ) -> None:
        # Determine required capability based on node name / tags
        required_cap = "pipeline:execute"
        if "train" in node.name.lower():
            required_cap = "model:train"
        elif "eval" in node.name.lower():
            required_cap = "model:evaluate"

        outcome = AuthorityValidator.validate(self._current_intent, required_cap)
        if not outcome.admitted:
            reasons = "; ".join(outcome.violations)
            console.print(f"[bold red]✖ Node '{node.name}' DENIED:[/bold red] {reasons}")
            if self.strict_mode:
                raise AdmissionDeniedError(f"Node '{node.name}' admission denied: {reasons}")
