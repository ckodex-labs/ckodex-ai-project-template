"""
Kedro Hook: Ray Cluster Lifecycle Management.
Ensures Ray runtime is initialized prior to pipeline execution and resources monitored.
"""

from __future__ import annotations

from typing import Any

from kedro.framework.hooks import hook_impl
from kedro.pipeline import Pipeline
from rich.console import Console

from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager

console = Console()


class RayLifecycleHook:
    """
    Manages Ray cluster initialization and shutdown during Kedro pipeline lifecycle.
    """

    def __init__(self, auto_shutdown: bool = False) -> None:
        self.auto_shutdown = auto_shutdown

    @hook_impl
    def before_pipeline_run(
        self,
        run_params: dict[str, Any],
        pipeline: Pipeline,
        catalog: Any,
    ) -> None:
        console.print("[bold cyan]⠹ Ray Hook:[/bold cyan] Initializing Ray runtime environment...")
        success = RayRuntimeManager.initialize()
        if success:
            info = RayRuntimeManager.get_cluster_info()
            console.print(
                f"[bold green]✔ Ray Cluster Active:[/bold green] {info.get('nodes')} nodes | "
                f"{info.get('cpus')} CPUs | {info.get('gpus')} GPUs | {info.get('memory_gb')} GB RAM"
            )
        else:
            console.print(
                "[bold red]✖ Ray Initialization Failed![/bold red] Fallback to local CPU execution."
            )

    @hook_impl
    def after_pipeline_run(
        self,
        run_params: dict[str, Any],
        pipeline: Pipeline,
        catalog: Any,
    ) -> None:
        if self.auto_shutdown:
            console.print("[cyan]Ray Hook: Shutting down Ray session...[/cyan]")
            RayRuntimeManager.shutdown()
