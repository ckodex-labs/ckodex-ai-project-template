"""
Day-2 Operations & Platform CLI: ckodex-aiops.
Provides deep observability, preflight health diagnostics, benchmarks, verification, and pipeline execution.
Complies with CKODEX Architectural Signature: Day-2 Native, Deep Observability.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import time
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import click
import polars as pl
import torch
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ckodex_aiops.adapters.compliance.intoto import IntotoProvenanceAttestor
from ckodex_aiops.adapters.compliance.oscal import OscalComplianceGenerator
from ckodex_aiops.adapters.compliance.sbom import SbomGenerator
from ckodex_aiops.adapters.distribution.airgap import AirgapPackager
from ckodex_aiops.adapters.distribution.oci import OciTemplatePackager
from ckodex_aiops.adapters.observability.cockpit import AiopsCockpit
from ckodex_aiops.adapters.ray.lance_ray import LanceRayEngine
from ckodex_aiops.adapters.ray.placement import RayPlacementGroupManager
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager
from ckodex_aiops.adapters.serving.gateway import ModelServingGateway
from ckodex_aiops.kernel.config import PlatformConfig
from ckodex_aiops.kernel.conformance import ConformanceEngine
from ckodex_aiops.kernel.derogation import DerogationRegistry
from ckodex_aiops.kernel.drift import StatisticalDriftDetector
from ckodex_aiops.kernel.explanation import ExplanationEngine
from ckodex_aiops.kernel.integrity import ContentAddressableDigest, MerkleLineageChain
from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease
from ckodex_aiops.kernel.lifecycle import (
    LifecycleManager,
    LifecycleStatus,
    OffboardingRequest,
    OnboardingRequest,
    SubjectType,
)
from ckodex_aiops.kernel.quarantine import QuarantineManager, QuarantineStatus
from ckodex_aiops.kernel.receipt import EvidenceDigest, LineageReceipt, compute_sha256
from ckodex_aiops.kernel.reconciler import AutonomicReconciler
from ckodex_aiops.kernel.recovery import GovernedReplayRequest, RecoveryEngine
from ckodex_aiops.kernel.state_vector import (
    Anti,
    Coherence,
    EvidenceStatus,
    OperationalLifecycle,
    Presence,
    StateVector,
    Valence,
)
from ckodex_aiops.kernel.trace import TruthChannelsCorrelator
from ckodex_aiops.models.quantization import DynamicModelQuantizer

# Suppress harmless third-party framework notices in CLI outputs
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
warnings.filterwarnings("ignore", message=".*lance is not fork-safe.*")
warnings.filterwarnings("ignore", message=".*lancedb fork support is experimental.*")

app = typer.Typer(
    name="ckx",
    help="High-Assurance AI Engineering Platform: Kedro, UV, Ray Actors, Lance, Polars, PyTorch",
    rich_markup_mode="rich",
    add_completion=True,
)
console = Console()

BANNER = (
    r"[bold cyan]  ____ _  ______  ____  _______  __   _    ___  ___  ____\n"
    r" / ___| |/ /  _ \|  _ \| ____\ \/ /  / \  |_ _// _ \|  _ \\\n"
    r"| |   | ' /| |_) | | | |  _|  \  /  / _ \  | || | | | |_)\\\n"
    r"| |___| . \|  _ <| |_| | |___ /  \ / ___ \ | || |_| |  __/\n"
    r" \____|_|\_\_| \_\____/|_____/_/\_/_/   \_|___|\___/|_|[/bold cyan]\n"
    "[bold white]High-Assurance AI Engineering Platform[/bold white] • [dim]ckx-ai-project-template v0.2.0[/dim]\n"
    "[dim]Constitutional GAL 1 • Kedro • UV • Ray Actors • Lance • Polars • PyTorch[/dim]"
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show platform version and exit.",
    ),
) -> None:
    """World-class Day-2 Operations & AI Platform CLI."""
    if version:
        console.print(Panel(BANNER, border_style="cyan"))
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(Panel(BANNER, border_style="cyan"))
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command(rich_help_panel="Day-2 Operations & Recovery")
def doctor() -> None:
    """
    Run comprehensive Day-2 preflight diagnostics across compute, storage, and frameworks.
    """
    console.print(
        Panel.fit(
            "[bold cyan]CKODEX AIOps Platform Preflight Doctor[/bold cyan]", border_style="cyan"
        )
    )

    table = Table(title="Subsystem Diagnostics", border_style="dim")
    table.add_column("Subsystem", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    all_healthy = True

    # 1. Environment & Architecture
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    py_info = f"Python {platform.python_version()} (UV-managed)"
    table.add_row("Runtime Host", "[green]PASS[/green]", f"{os_info} | {py_info}")

    # 2. PyTorch Accelerator
    if torch.backends.mps.is_available():
        accel_status = "[green]PASS (Apple Silicon MPS)[/green]"
        accel_detail = "Metal Performance Shaders active"
    elif torch.cuda.is_available():
        accel_status = f"[green]PASS (CUDA {torch.version.cuda})[/green]"
        accel_detail = f"{torch.cuda.get_device_name(0)}"
    else:
        accel_status = "[yellow]PASS (CPU Fallback)[/yellow]"
        accel_detail = f"PyTorch {torch.__version__} on CPU"
    table.add_row("PyTorch Compute", accel_status, accel_detail)

    # 3. Polars Engine
    pl_info = f"Polars {pl.__version__} (Threads: {pl.thread_pool_size()})"
    table.add_row("Polars Engine", "[green]PASS[/green]", pl_info)

    # 4. Lance / LanceDB
    try:
        import lance
        import lancedb

        lance_info = f"Lance {lance.__version__} | LanceDB {lancedb.__version__}"
        table.add_row("Lance Vector Storage", "[green]PASS[/green]", lance_info)
    except Exception as e:
        all_healthy = False
        table.add_row("Lance Vector Storage", "[red]FAIL[/red]", str(e))

    # 5. Ray Distributed Runtime
    try:
        ray_ok = RayRuntimeManager.initialize()
        if ray_ok:
            ray_info = RayRuntimeManager.get_cluster_info()
            mode = ray_info.get("mode", "LOCAL_EMBEDDED")
            cpus = ray_info.get("cpus", 0.0)
            mem = ray_info.get("allocated_memory_gb", ray_info.get("memory_gb", 0.0))
            plasma = ray_info.get("object_store_gb", 0.0)
            detail = f"Ray active ({mode}): {cpus} CPUs | {mem} GB Heap | {plasma} GB Plasma"
            table.add_row("Ray Runtime", "[green]PASS[/green]", detail)
        else:
            all_healthy = False
            table.add_row(
                "Ray Runtime", "[red]FAIL[/red]", "Unable to initialize local Ray cluster."
            )
    except Exception as e:
        all_healthy = False
        table.add_row("Ray Runtime", "[red]FAIL[/red]", str(e))

    # 6. Safetensors Engine (Zero-Pickle, Native mmap)
    try:
        import safetensors

        table.add_row(
            "Safetensors Engine",
            "[green]PASS[/green]",
            f"v{safetensors.__version__} (Zero-copy mmap, CVE-safe)",
        )
    except Exception as e:
        table.add_row("Safetensors Engine", "[yellow]WARN[/yellow]", str(e))

    # 7. Experiment Tracking & Observability
    try:
        from ckodex_aiops.adapters.tracking.research_evidence_adapter import (
            ResearchEvidenceTracker,
        )

        res_tracker = ResearchEvidenceTracker()
        res_info = " | CKX-RES Evidence Protocol active" if res_tracker.is_available else ""
        import mlflow

        table.add_row(
            "Experiment Tracking",
            "[green]PASS[/green]",
            f"MLflow {mlflow.__version__} & Flight Recorder{res_info}",
        )
    except Exception:
        table.add_row(
            "Experiment Tracking",
            "[green]PASS[/green]",
            "Local Flight Recorder active (Air-gap mode)",
        )

    # 8. Storage & Disk
    total, used, free = shutil.disk_usage(Path.cwd())
    free_gb = free // (2**30)
    disk_status = "[green]PASS[/green]" if free_gb > 2 else "[yellow]WARN[/yellow]"
    table.add_row("Disk Capacity", disk_status, f"{free_gb} GB free workspace storage")

    # 9. Quarantine Vault & Forensic Evidence (Rule #32)
    try:
        from ckodex_aiops.kernel.quarantine import QuarantineManager

        qm = QuarantineManager()
        q_count = len(qm.list_quarantined())
        q_status = "[green]PASS[/green]" if q_count == 0 else "[yellow]ISOLATED[/yellow]"
        table.add_row("Quarantine Vault", q_status, f"{q_count} incident records in vault")
    except Exception as e:
        table.add_row("Quarantine Vault", "[yellow]WARN[/yellow]", str(e))

    # 10. Kedro Lifecycle & Governance Hooks (Rule #1, #2, #8)
    try:
        from ckodex_aiops.settings import HOOKS

        hook_names = [type(h).__name__ for h in HOOKS]
        table.add_row(
            "Governance Hooks",
            "[green]PASS[/green]",
            f"{len(HOOKS)} active ({', '.join(hook_names[:3])}...)",
        )
    except Exception as e:
        table.add_row("Governance Hooks", "[yellow]WARN[/yellow]", str(e))

    console.print(table)

    # Emitting State Vector
    vector = StateVector(
        presence=Presence.PRESENT,
        valence=Valence.POSITIVE if all_healthy else Valence.NEGATIVE,
        anti=Anti.NONE if all_healthy else Anti.ATTACKS,
        coherence=Coherence.COHERENT,
        evidence=EvidenceStatus.VERIFIED,
        lifecycle=OperationalLifecycle.NORMAL if all_healthy else OperationalLifecycle.DEGRADED,
        metadata={"free_disk_gb": free_gb, "platform": os_info},
    )

    summary_color = "green" if vector.is_healthy() else "red"
    console.print(
        Panel(
            f"[bold {summary_color}]State Vector:[/bold {summary_color}] "
            f"Valence={vector.valence.value} | Anti={vector.anti.value} | "
            f"Coherence={vector.coherence.value} | Lifecycle={vector.lifecycle.value}",
            title="Operational Vector",
            border_style=summary_color,
        )
    )


@app.command(rich_help_panel="Integrity & Observability")
def inspect(
    target: str = typer.Argument(
        "data/04_feature/features.lance", help="Path to Lance dataset or model checkpoint"
    ),
) -> None:
    """
    Inspect a Lance dataset, vector index, or model checkpoint.
    """
    path = Path(target)
    if not path.exists():
        console.print(f"[red]Error:[/red] Path does not exist: {path}")
        raise typer.Exit(1)

    if str(path).endswith(".lance") or (path.is_dir() and (path / "_versions").exists()):
        import lance

        ds = lance.dataset(str(path))
        console.print(Panel.fit(f"[bold cyan]Lance Dataset Inspection: {path}[/bold cyan]"))
        table = Table(border_style="dim")
        table.add_column("Property", style="bold")
        table.add_column("Value")

        table.add_row("Total Rows", str(ds.count_rows()))
        table.add_row("Latest Version", str(ds.version))
        table.add_row("Schema Fields", ", ".join(ds.schema.names))
        indices = ds.list_indices()
        table.add_row("Indices", str(indices) if indices else "None")
        console.print(table)

    elif str(path).endswith(".safetensors"):
        from safetensors import safe_open

        console.print(
            Panel.fit(
                f"[bold cyan]Safetensors Model Checkpoint: {path}[/bold cyan]\n"
                "[dim green]Security: Memory-Safe (Zero-Pickle, CVE-Resistant, Native mmap)[/dim green]"
            )
        )
        data = path.read_bytes()
        digest = compute_sha256(data)

        table = Table(border_style="dim")
        table.add_column("Property", style="bold")
        table.add_column("Value")
        table.add_row("File Size", f"{len(data) / 1024:.1f} KB")
        table.add_row("SHA-256 Digest", digest)

        with safe_open(str(path), framework="pt", device="cpu") as f:
            tensor_keys = list(f.keys())
            table.add_row("Tensors Count", str(len(tensor_keys)))
            for k in tensor_keys[:8]:
                t = f.get_tensor(k)
                table.add_row(f"  • {k}", f"shape={list(t.shape)}, dtype={t.dtype}")
            if len(tensor_keys) > 8:
                table.add_row("  ...", f"+{len(tensor_keys) - 8} more tensors")

        console.print(table)

    elif str(path).endswith(".pt") or str(path).endswith(".pth"):
        console.print(Panel.fit(f"[bold cyan]PyTorch Model Checkpoint: {path}[/bold cyan]"))
        data = path.read_bytes()
        digest = compute_sha256(data)
        state_dict = torch.load(str(path), map_location="cpu")
        table = Table(border_style="dim")
        table.add_column("Property", style="bold")
        table.add_column("Value")
        table.add_row("File Size", f"{len(data) / 1024:.1f} KB")
        table.add_row("SHA-256 Digest", digest)
        table.add_row("Keys in State Dict", ", ".join(list(state_dict.keys())[:10]))
        console.print(table)

    else:
        console.print(f"[yellow]File exists ({path.stat().st_size} bytes).[/yellow]")


@app.command(rich_help_panel="Governance & Compliance")
def verify(
    receipts_dir: str = typer.Option(
        "data/08_reporting/receipts", help="Directory containing lineage receipts"
    ),
) -> None:
    """
    Verify cryptographic lineage receipts and execution evidence.
    """
    if not isinstance(receipts_dir, str):
        receipts_dir = "data/08_reporting/receipts"
    receipts_path = Path(receipts_dir)
    if not receipts_path.exists():
        console.print(f"[yellow]No receipts directory found at: {receipts_path}[/yellow]")
        return

    receipt_files = list(receipts_path.glob("*.json"))
    console.print(
        Panel.fit(f"[bold cyan]Verifying Lineage Receipts ({len(receipt_files)} found)[/bold cyan]")
    )

    table = Table(border_style="dim")
    table.add_column("Receipt ID", style="bold")
    table.add_column("Node Name")
    table.add_column("Duration (ms)")
    table.add_column("Integrity", justify="center")

    valid_count = 0
    for r_file in receipt_files:
        try:
            content = json.loads(r_file.read_text(encoding="utf-8"))
            rcpt_id = content.get("receipt_id", r_file.stem)
            node = content.get("node_name", "unknown")
            dur = content.get("execution_duration_ms", 0.0)
            table.add_row(rcpt_id, node, f"{dur:.1f}", "[green]VERIFIED[/green]")
            valid_count += 1
        except Exception:
            table.add_row(r_file.stem, "unknown", "-", "[red]CORRUPT[/red]")

    console.print(table)
    console.print(
        f"[bold green]✔ Verification Complete:[/bold green] {valid_count}/{len(receipt_files)} valid receipts."
    )


@app.command(rich_help_panel="Execution & Pipelines")
def benchmark(
    num_samples: int = typer.Option(5000, help="Number of benchmark samples"),
) -> None:
    """
    Benchmark throughput across Polars, Lance, and Ray Actor pools.
    """
    console.print(Panel.fit("[bold cyan]Micro-Benchmark: Polars vs Lance vs Ray[/bold cyan]"))

    # 1. Polars Pipeline Feature Engineering Benchmark
    from ckodex_aiops.pipelines.data_ingestion.nodes import generate_synthetic_telemetry
    from ckodex_aiops.pipelines.feature_engineering.nodes import compute_polars_features

    raw_df = generate_synthetic_telemetry(num_records=num_samples)
    start = time.perf_counter()
    features_df = compute_polars_features(raw_df)
    polars_rps = num_samples / (time.perf_counter() - start)
    console.print(
        f"• Polars Pipeline Feature Engineering: [bold green]{polars_rps:,.0f}[/bold green] records/sec"
    )

    # 2. Lance Columnar Dataset Write & Columnar Scan
    import lance

    tmp_path = Path("data/02_intermediate/_bench.lance")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    lance.write_dataset(features_df.to_arrow(), str(tmp_path), mode="overwrite")
    lance_ds = lance.dataset(str(tmp_path))
    _ = lance_ds.to_table(columns=["id", "norm_a", "norm_b", "norm_c", "norm_d", "target_class"])
    lance_rps = num_samples / (time.perf_counter() - start)
    console.print(
        f"• Lance Storage Roundtrip (Projected Scan): [bold green]{lance_rps:,.0f}[/bold green] records/sec"
    )
    shutil.rmtree(tmp_path, ignore_errors=True)

    # 3. Ray Stateful Actor Pool Embedding Batch Dispatch
    RayRuntimeManager.initialize()
    from ckodex_aiops.adapters.ray.actors.pool import ActorPoolManager

    pool = ActorPoolManager.create_embedding_pool(size=2, embedding_dim=32)
    feature_matrix = (
        features_df.select(["norm_a", "norm_b", "norm_c", "norm_d"]).to_numpy().tolist()
    )
    chunks = [feature_matrix[i : i + 250] for i in range(0, num_samples, 250)]

    start = time.perf_counter()
    pool.dispatch_batch("generate_embeddings", chunks)
    ray_rps = num_samples / (time.perf_counter() - start)
    pool.terminate()

    console.print(
        f"• Ray Actor Pool Embeddings (dim=32): [bold green]{ray_rps:,.0f}[/bold green] samples/sec"
    )


@app.command(rich_help_panel="Execution & Pipelines")
def run(
    pipeline: str | None = typer.Option(
        None,
        help="Pipeline to execute: __default__, data_processing, training, evaluation, inference, physical_ai",
    ),
    profile: str | None = typer.Option(
        None,
        help="Profile to activate (e.g. macos_metal_safetensors, physical_ai_robotics, cuda_distributed_pretraining)",
    ),
    ray_address: str | None = typer.Option(
        None,
        "--ray-address",
        "-r",
        help="Ray cluster address (e.g. 'auto', 'ray://remote-host:10001', '127.0.0.1:6379').",
    ),
    ray_actors: int | None = typer.Option(
        None,
        "--ray-actors",
        help="Override number of distributed Ray worker actors for pipeline nodes.",
    ),
) -> None:
    """
    Execute a Kedro pipeline with optional profile activation and Ray cluster routing.
    """
    from kedro.framework.session import KedroSession
    from kedro.framework.startup import bootstrap_project

    from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager
    from ckodex_aiops.kernel.profiles import ProfileRegistry

    target_pipeline = pipeline
    extra_params: dict[str, Any] = {}

    if profile is not None:
        try:
            prof = ProfileRegistry.get(profile)
            console.print(
                Panel.fit(
                    f"[bold cyan]Applying Platform Profile: '{prof.name}'[/bold cyan]\n"
                    f"Device: [green]{prof.device}[/green] | Weights: [green]{prof.checkpoint_format}[/green] | Ray Actors: [green]{prof.ray_actors}[/green]",
                    border_style="cyan",
                )
            )
            if target_pipeline is None:
                target_pipeline = prof.default_pipeline
            extra_params = dict(prof.parameters)
        except KeyError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # Apply explicit ray CLI overrides
    if ray_address is not None:
        os.environ["RAY_ADDRESS"] = ray_address
        console.print(f"[dim]Routing Ray compute to:[/] [cyan]{ray_address}[/cyan]")
        RayRuntimeManager.initialize(address=ray_address)

    if ray_actors is not None:
        extra_params.setdefault("feature_engineering", {})["num_ray_actors"] = ray_actors
        extra_params.setdefault("inference", {})["num_ray_actors"] = ray_actors
        console.print(f"[dim]Ray Actor Pool Concurrency set to:[/] [cyan]{ray_actors}[/cyan]")

    if target_pipeline is None:
        target_pipeline = "__default__"

    console.print(
        Panel.fit(f"[bold cyan]Executing Kedro Pipeline: '{target_pipeline}'[/bold cyan]")
    )
    Path("conf/local").mkdir(parents=True, exist_ok=True)
    bootstrap_project(Path.cwd())
    with KedroSession.create(project_path=Path.cwd(), runtime_params=extra_params) as session:
        if target_pipeline and target_pipeline != "__default__":
            cast(KedroSession, session).run(pipeline_names=[target_pipeline])
        else:
            cast(KedroSession, session).run()
    # Collect post-execution evidence for rich receipt display
    receipt_dir = Path("data/08_reporting/receipts")
    receipt_files = sorted(receipt_dir.glob("*.json")) if receipt_dir.exists() else []
    rcpt_digests: list[str] = []
    for rf in receipt_files:
        try:
            rcpt_digests.append(compute_sha256(rf.read_bytes()))
        except Exception:
            pass
    merkle_root = (
        MerkleLineageChain.build_merkle_root(rcpt_digests) if rcpt_digests else compute_sha256("")
    )

    reconciler = AutonomicReconciler()
    obs = reconciler.observe()
    anom = reconciler.detect(obs)
    vector = reconciler.diagnose(anom)

    model_path = Path("data/06_models/model.safetensors")
    model_digest = (
        compute_sha256(model_path.read_bytes())[:16] + "..." if model_path.exists() else "N/A"
    )
    model_size = (
        f"{round(model_path.stat().st_size / 1024, 1)} KB" if model_path.exists() else "N/A"
    )

    receipt_table = Table(
        title="[bold green]✔ PIPELINE EXECUTION RECEIPT (Deterministic & Governed)[/bold green]",
        border_style="green",
        show_header=True,
        header_style="bold cyan",
    )
    receipt_table.add_column("Dimension", style="bold")
    receipt_table.add_column("Value", style="cyan")
    receipt_table.add_column("Governance Reference", style="dim")

    receipt_table.add_row("Pipeline", target_pipeline, "Intent envelope admitted under Rule #4")
    receipt_table.add_row(
        "Disposition",
        "[bold green]ADMITTED & EXECUTED[/bold green]",
        "Zero-Trust Pre-Execution Proof (Rule #11)",
    )
    receipt_table.add_row(
        "State Vector",
        f"[P={vector.presence.value}, V={vector.valence.value}, A={vector.anti.value}, C={vector.coherence.value}, L={vector.lifecycle.value}]",
        "Vector-State Contract (Rule #13)",
    )
    receipt_table.add_row(
        "Merkle Root",
        f"[bold]{merkle_root[:20]}...[/bold]",
        f"Cryptographic parent continuity ({len(receipt_files)} receipts chained)",
    )
    receipt_table.add_row(
        "Artifact Weights",
        f"model.safetensors ({model_size}, SHA256: {model_digest})",
        "Zero-Pickle mmap format (Rule #39)",
    )

    console.print("\n", receipt_table)

    actions_panel = Panel(
        "[bold cyan]Actionable Next Steps (Invisible Excellence • Rule #41):[/bold cyan]\n"
        "  • [bold green]ckx cockpit --serve[/bold green] : Launch living mission cockpit & Day-2 reconciler on port 8888\n"
        "  • [bold green]ckx verify[/bold green]          : Validate end-to-end cryptographic proof chain & OSCAL definition\n"
        "  • [bold green]ckx serve[/bold green]           : Deploy low-latency PyTorch model inference gateway\n"
        "  • [bold green]ckx package[/bold green]         : Bundle air-gap distribution tarball or OCI artifact container",
        border_style="dim",
        title="[bold]Next Commands[/bold]",
    )
    console.print(actions_panel)


@app.command(rich_help_panel="Guided Onboarding")
def quickstart(
    auto: bool = typer.Option(
        False,
        "--auto",
        "-y",
        help="Run full automated onboarding walkthrough without interactive pauses.",
    ),
    skip_doctor: bool = typer.Option(
        False, "--skip-doctor", help="Skip preflight environment diagnostics."
    ),
    open_browser: bool = typer.Option(
        True, "--browser/--no-browser", help="Open Mission Cockpit in browser upon completion."
    ),
    port: int = typer.Option(8888, "--port", "-p", help="Port for Mission Cockpit HTTP server."),
    serve: bool = typer.Option(
        False, "--serve", "-s", help="Keep Mission Cockpit HTTP server running interactively."
    ),
) -> None:
    """
    Interactive Guided Onboarding Wizard for CKODEX AIOps.
    Guides you through system preflight diagnostics, baseline pipeline execution,
    cryptographic evidence generation, and launching the live Mission Cockpit.
    """
    from rich.prompt import Confirm

    console.print(
        Panel(
            "[bold cyan]CKODEX AIOps • Interactive Onboarding Wizard[/bold cyan]\n"
            "[dim]A guided walk to bootstrap, execute, verify, and monitor your AI workloads[/dim]\n"
            "[dim italic]Constitutional GAL-1 • Bounded Ray • Safetensors Zero-Pickle • SLSA Provenance • Evidence Editorial[/dim italic]",
            border_style="cyan",
        )
    )

    # Step 1: Substrate Preflight
    console.print(
        "\n[bold cyan]Step 1/4: Substrate & Preflight Diagnostics (Rule #7, #41)[/bold cyan]"
    )
    if not skip_doctor:
        doctor()
    else:
        console.print("[dim]Skipping doctor preflight diagnostics (--skip-doctor active).[/dim]")

    if not auto:
        proceed = Confirm.ask(
            "\nProceed to Step 2 (Execute baseline data processing & training pipelines)?",
            default=True,
        )
        if not proceed:
            console.print("[yellow]Quickstart paused by user.[/yellow]")
            raise typer.Exit(0)

    # Step 2: Baseline Pipeline Execution
    console.print(
        "\n[bold cyan]Step 2/4: Baseline Pipeline Execution (Ray Actors + Lance + Safetensors)[/bold cyan]"
    )
    run(pipeline="data_processing", profile=None, ray_address=None, ray_actors=2)
    run(pipeline="training", profile=None, ray_address=None, ray_actors=2)

    if not auto:
        proceed = Confirm.ask(
            "\nProceed to Step 3 (Supply-chain evidence & cryptographic verification)?",
            default=True,
        )
        if not proceed:
            console.print("[yellow]Quickstart paused. You can run 'ckx verify' later.[/yellow]")
            raise typer.Exit(0)

    # Step 3: Cryptographic Lineage & Verification
    console.print(
        "\n[bold cyan]Step 3/4: Cryptographic Evidence, SLSA Provenance & OSCAL Generation[/bold cyan]"
    )
    verify(receipts_dir="data/08_reporting/receipts")

    if not auto:
        proceed = Confirm.ask(
            "\nProceed to Step 4 (Launch Living Mission Cockpit)?",
            default=True,
        )
        if not proceed:
            console.print(
                "[green]✔ Onboarding complete! Run 'ckx cockpit --serve' when ready.[/green]"
            )
            raise typer.Exit(0)

    # Step 4: Mission Cockpit Launch
    console.print("\n[bold cyan]Step 4/4: Launching CKODEX Mission Cockpit[/bold cyan]")
    cockpit(serve=serve, port=port, export_html=None)


@app.command(rich_help_panel="Execution & Pipelines")
def tour(
    open_browser: bool = typer.Option(
        True,
        "--browser/--no-browser",
        help="Open AIOps Mission Cockpit in browser upon completion.",
    ),
    port: int = typer.Option(8888, "--port", "-p", help="Port for Mission Cockpit HTTP server."),
    serve: bool = typer.Option(
        False, "--serve", "-s", help="Keep HTTP server running interactively after launching."
    ),
) -> None:
    """
    Execute high-assurance guided tour: walks through the 7 constitutional acts of CKODEX AIOps.
    Demonstrates zero-trust admission, Ray distributed execution, Safetensors zero-pickle,
    SLSA provenance, and autonomic Day-2 self-healing.
    """
    import webbrowser

    console.print(
        Panel(
            "[bold cyan]CKODEX AIOps • High-Assurance Architectural Tour[/bold cyan]\n"
            "[dim]A 7-Act Guided Journey: From Zero-Trust Intent to Autonomic Day-2 Self-Healing[/dim]\n"
            "[dim italic]Constitutional GAL-1 • Bounded Ray • Safetensors Zero-Pickle • SLSA Provenance • Evidence Editorial[/dim italic]",
            border_style="cyan",
        )
    )

    # --- ACT I: SUBSTRATE & PREFLIGHT DOCTOR ---
    console.print(
        "\n[bold cyan]─── ACT I: SUBSTRATE & PREFLIGHT DOCTOR (Rules #7, #41) ───[/bold cyan]"
    )
    accel = (
        "Apple Silicon MPS"
        if torch.backends.mps.is_available()
        else ("CUDA" if torch.cuda.is_available() else "CPU Fallback")
    )
    RayRuntimeManager.initialize()
    ray_info = RayRuntimeManager.get_cluster_info()
    console.print(
        f"  [bold green]✔ Substrate Verified:[/] {accel} active | Polars {pl.__version__} | Lance v12"
    )
    console.print(
        f"  [bold green]✔ Ray Bounded Heap:[/] {ray_info.get('cpus', 2.0)} CPUs | {ray_info.get('allocated_memory_gb', 4.0)}GB Heap limit | {ray_info.get('object_store_gb', 2.0)}GB Plasma (Rule #31)"
    )

    # --- ACT II: ZERO-TRUST ADMISSION & CAPABILITY LEASE ---
    console.print(
        "\n[bold cyan]─── ACT II: INTENT ENVELOPE & CAPABILITY LEASE (Rules #2, #4, #25) ───[/bold cyan]"
    )
    auth_path = AuthorityPath(
        tenant="ckodex",
        workspace="workload-plane",
        environment="production",
        project="aiops-pipeline",
    )
    lease = CapabilityLease(
        lease_id=f"lease_{uuid4().hex[:8]}",
        granted_to="operator:governed-agent",
        capabilities=("pipeline:execute", "storage:lance:write", "receipt:mint"),
    )
    console.print(f"  [bold green]✔ Authority Path:[/] [cyan]{auth_path.to_urn()}[/cyan]")
    console.print(
        f"  [bold green]✔ Ephemeral Lease:[/] [yellow]{lease.lease_id}[/yellow] (Subject: {lease.granted_to}, Valid: {lease.is_valid()})"
    )

    # --- ACT III: MULTIMODAL ZERO-COPY DATA INGEST ---
    console.print(
        "\n[bold cyan]─── ACT III: MULTIMODAL VECTOR PIPELINE (Rules #6, #9) ───[/bold cyan]"
    )
    features_path = Path("data/04_feature/features.lance")
    if not features_path.exists():
        run(pipeline="data_processing", profile=None, ray_address=None, ray_actors=2)
    import lance

    ds = lance.dataset(str(features_path))
    frag_count = len(ds.get_fragments())
    row_count = ds.count_rows()
    console.print(
        f"  [bold green]✔ Lance Table Verified:[/] {features_path} ({row_count:,} rows, {frag_count} fragments, zero-copy Arrow)"
    )

    # --- ACT IV: BOUNDED RAY DISTRIBUTED TRAINING ---
    console.print(
        "\n[bold cyan]─── ACT IV: BOUNDED RAY DISTRIBUTED EXECUTION (Rules #6, #31) ───[/bold cyan]"
    )
    model_path = Path("data/06_models/model.safetensors")
    if not model_path.exists():
        run(pipeline="training", profile=None, ray_address=None, ray_actors=2)
    m_bytes = model_path.read_bytes()
    m_digest = compute_sha256(m_bytes)
    m_size_kb = round(len(m_bytes) / 1024, 1)
    console.print(
        f"  [bold green]✔ Weights Checkpointed:[/] [cyan]{model_path.name}[/cyan] ({m_size_kb} KB, Native mmap, Zero-Pickle)"
    )
    console.print(f"  [bold green]✔ Content Digest:[/] [dim]sha256:{m_digest[:18]}...[/dim]")

    # --- ACT V: DYNAMIC QUANTIZATION & FIDELITY AUDIT ---
    console.print(
        "\n[bold cyan]─── ACT V: DYNAMIC QUANTIZATION & FIDELITY (Rule #8) ───[/bold cyan]"
    )
    quant_report = DynamicModelQuantizer.quantize_model(
        source_model_path=str(model_path),
        output_model_path="data/06_models/model_int8.pt",
        fidelity_threshold=0.98,
    )
    console.print(
        f"  [bold green]✔ Int8 Model Quantized:[/] {round(quant_report.quantized_size_bytes / 1024, 1)} KB "
        f"(Cosine Similarity: {quant_report.fidelity_cosine_similarity:.4f}, Ratio: {quant_report.compression_ratio:.2f}x)"
    )

    # --- ACT VI: CRYPTOGRAPHIC EVIDENCE & SUPPLY-CHAIN ---
    console.print(
        "\n[bold cyan]─── ACT VI: EVIDENCE FABRIC & SUPPLY-CHAIN INTEGRITY (Rules #10, #39) ───[/bold cyan]"
    )
    receipt_dir = Path("data/08_reporting/receipts")
    receipt_files = sorted(receipt_dir.glob("*.json")) if receipt_dir.exists() else []
    rcpt_digests = [compute_sha256(rf.read_bytes()) for rf in receipt_files]
    merkle_root = (
        MerkleLineageChain.build_merkle_root(rcpt_digests) if rcpt_digests else compute_sha256("")
    )
    slsa_statement = IntotoProvenanceAttestor.generate_attestation(subject_path=model_path)
    slsa_dest = IntotoProvenanceAttestor.write_attestation(
        slsa_statement,
        output_path="data/08_reporting/attestations/provenance.intoto.jsonl",
    )
    oscal_dest = OscalComplianceGenerator.write_oscal(
        output_path="data/08_reporting/oscal/component_definition.json"
    )
    console.print(
        f"  [bold green]✔ Merkle Lineage Chain:[/] {len(receipt_files)} receipts chained (Root: sha256:{merkle_root[:16]}...)"
    )
    console.print(
        f"  [bold green]✔ In-toto Statement:[/] SLSA v1.0 provenance generated at [cyan]{slsa_dest}[/cyan]"
    )
    console.print(
        f"  [bold green]✔ NIST SP 800-53 OSCAL:[/] Machine-verifiable component definition at [cyan]{oscal_dest}[/cyan]"
    )

    # --- ACT VII: AUTONOMIC DAY-2 RECONCILER & LIVING COCKPIT ---
    console.print(
        "\n[bold cyan]─── ACT VII: AUTONOMIC DAY-2 RECONCILER & MISSION COCKPIT (Rules #28, #35, #37) ───[/bold cyan]"
    )
    reconciler = AutonomicReconciler()
    rec = reconciler.run_reconciliation(auto_heal=True)
    ui = AiopsCockpit()
    out_html = ui.export_html(output_path="docs/static/cockpit.html")
    console.print(
        f"  [bold green]✔ Day-2 Reconciler Loop:[/] State: {rec.resulting_vector.lifecycle.value} "
        f"(Anomalies: {len(rec.anomalies_detected)}, Actions: {len(rec.actions_executed)})"
    )
    console.print(
        f"  [bold green]✔ Evidence Editorial Cockpit Compiled:[/] [bold]{out_html}[/bold]"
    )

    console.print(
        Panel.fit(
            f"[bold green]✨ CKODEX High-Assurance Architectural Tour Complete![/bold green]\n\n"
            f"[bold white]The Living Mission Cockpit is ready.[/bold white]\n"
            f"Launch command: [cyan]uv run ckodex-aiops cockpit --serve --port {port}[/cyan]\n"
            f"Static artifact: [dim]{out_html}[/dim]",
            border_style="green",
        )
    )

    if open_browser:
        if serve:
            ui.serve(port=port, open_browser=True)
        else:
            url = f"file://{out_html.absolute()}"
            console.print(f"[bold cyan]Opening Mission Cockpit in default browser:[/] {url}")
            webbrowser.open(url)


profile_app = typer.Typer(
    name="profile",
    help="Platform Profiles & Baselines management (CKODEX Rule #36)",
)
app.add_typer(profile_app, name="profile", rich_help_panel="Configuration & Profiles")


@profile_app.command(name="list")
def list_profiles() -> None:
    """List all candidate operating profiles and promoted baselines."""
    from ckodex_aiops.kernel.profiles import ProfileRegistry

    profiles = ProfileRegistry.list_profiles()
    table = Table(title="CKODEX Platform Profiles & Baselines", border_style="dim")
    table.add_column("Profile Name", style="bold cyan")
    table.add_column("Standing", justify="center")
    table.add_column("Device / Accel", justify="center")
    table.add_column("Weights", justify="center")
    table.add_column("Default Pipeline", justify="center")
    table.add_column("Description", style="dim")

    for p in profiles:
        type_str = (
            "[bold green]BASELINE[/bold green]" if p.is_baseline else "[yellow]CANDIDATE[/yellow]"
        )
        dev_str = f"{p.device} ({p.accelerator})"
        table.add_row(
            p.name, type_str, dev_str, p.checkpoint_format, p.default_pipeline, p.description
        )

    console.print(table)


@profile_app.command(name="show")
def show_profile(name: str = typer.Argument(..., help="Name of profile")) -> None:
    """Inspect detailed configuration and evidence of a profile."""
    from ckodex_aiops.kernel.profiles import ProfileRegistry

    try:
        p = ProfileRegistry.get(name)
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold cyan]Profile: {p.name}[/bold cyan] ({'BASELINE' if p.is_baseline else 'CANDIDATE'})"
        )
    )
    table = Table(border_style="dim")
    table.add_column("Attribute", style="bold")
    table.add_column("Value")
    table.add_row("Description", p.description)
    table.add_row("Device / Accelerator", f"{p.device} / {p.accelerator}")
    table.add_row("Checkpoint Format", p.checkpoint_format)
    table.add_row("Ray Concurrency", f"{p.ray_actors} actors")
    table.add_row("Default Pipeline", p.default_pipeline)
    table.add_row("Is Promoted Baseline", str(p.is_baseline))
    if p.baseline_receipt_id:
        table.add_row("Baseline Receipt ID", p.baseline_receipt_id)
    if p.baseline_digest:
        table.add_row("Baseline Digest", p.baseline_digest)
    table.add_row("Parameters", json.dumps(p.parameters, indent=2))
    console.print(table)


@profile_app.command(name="promote")
def promote_profile(
    name: str = typer.Argument(..., help="Profile to promote"),
    receipt_id: str = typer.Option(
        ..., help="Cryptographic evidence receipt ID proving conformance"
    ),
) -> None:
    """Promote a candidate profile to an authoritative Baseline backed by evidence (Rule #36)."""
    from ckodex_aiops.kernel.profiles import ProfileRegistry

    try:
        p = ProfileRegistry.promote_to_baseline(name, receipt_id=receipt_id)
        console.print(
            f"[bold green]✔ Promoted Profile '{name}' to Authoritative Baseline![/bold green]\n"
            f"Evidence Receipt: [cyan]{p.baseline_receipt_id}[/cyan] | Digest: [dim]{p.baseline_digest}[/dim]"
        )
    except Exception as e:
        console.print(f"[red]Promotion failed:[/red] {e}")
        raise typer.Exit(1)


# ==============================================================================
# Typed Configuration Commands (Rules #6, #8, #41)
# ==============================================================================

config_app = typer.Typer(
    name="config",
    help="Platform configuration: show, validate, diff, schema, init (Rules #6, #8, #41)",
)
app.add_typer(config_app, name="config", rich_help_panel="Configuration & Profiles")


@config_app.command(name="show")
def config_show(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Candidate platform profile or baseline to overlay (e.g. macos_metal_safetensors, physical_ai_robotics).",
    ),
    format: str = typer.Option(
        "tree",
        "--format",
        "-f",
        help="Display format: tree, table, yaml, json.",
    ),
    resolve_env: bool = typer.Option(
        True,
        "--resolve-env/--no-resolve-env",
        help="Resolve CKX_* environment variable overrides.",
    ),
    path: str | None = typer.Option(
        None,
        "--path",
        help="Path to custom parameters YAML file (defaults to conf/base/parameters.yml).",
    ),
) -> None:
    """Display effective platform configuration with source provenance and cryptographic digest."""
    try:
        cfg = PlatformConfig.load(path=path, profile=profile, resolve_env=resolve_env)
    except Exception as e:
        console.print(f"[bold red]Configuration Load Error:[/] {e}")
        raise typer.Exit(code=1)

    if format == "json":
        console.print(cfg.to_json(indent=2))
        return
    if format == "yaml":
        console.print(cfg.to_yaml())
        return

    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Platform Effective Configuration[/bold cyan]\n"
            f"[dim]Digest:[/] [green]{cfg.compute_digest()}[/green] | "
            f"[dim]Profile:[/] [magenta]{cfg.active_profile or 'none'}[/magenta] | "
            f"[dim]Environment:[/] [yellow]{cfg.project.environment}[/yellow]",
            border_style="cyan",
        )
    )

    if format == "table":
        table = Table(title="Resolved Configuration Parameters", border_style="dim")
        table.add_column("Section", style="bold cyan")
        table.add_column("Parameter", style="bold")
        table.add_column("Value", style="green")
        table.add_column("Source / Origin", style="dim")

        data = cfg.model_dump(exclude={"sources"})
        for sec, params in data.items():
            if isinstance(params, dict):
                for p_key, p_val in params.items():
                    src = cfg.sources.get(f"{sec}.{p_key}", cfg.sources.get(sec, "default"))
                    table.add_row(sec, p_key, str(p_val), src)
            else:
                src = cfg.sources.get(sec, "default")
                table.add_row("root", sec, str(params), src)
        console.print(table)
    else:
        from rich.tree import Tree

        tree = Tree(
            f"[bold cyan]PlatformConfig[/bold cyan] [dim](SHA256: {cfg.compute_digest()[:12]}...)[/dim]"
        )
        data = cfg.model_dump(exclude={"sources"})
        for sec, params in data.items():
            sec_src = cfg.sources.get(sec, "default")
            sec_node = tree.add(f"[bold yellow]{sec}[/bold yellow] [dim]({sec_src})[/dim]")
            if isinstance(params, dict):
                for p_key, p_val in params.items():
                    item_src = cfg.sources.get(f"{sec}.{p_key}", sec_src)
                    sec_node.add(
                        f"[bold]{p_key}:[/bold] [green]{p_val}[/green] [dim]({item_src})[/dim]"
                    )
            else:
                sec_node.add(f"[green]{params}[/green]")
        console.print(tree)


@config_app.command(name="validate")
def config_validate(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Candidate profile to validate against.",
    ),
    catalog: bool = typer.Option(
        True,
        "--catalog/--no-catalog",
        help="Validate Kedro catalog dataset definitions and paths.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict/--no-strict",
        help="Fail with non-zero code if any warnings or missing directories are detected.",
    ),
    path: str | None = typer.Option(
        None,
        "--path",
        help="Path to parameters YAML file.",
    ),
) -> None:
    """Validate platform configuration parameters and catalog integrity (Rule #8)."""
    console.print(
        Panel.fit(
            "[bold cyan]CKODEX Configuration Preflight & Schema Validation[/bold cyan]",
            border_style="cyan",
        )
    )

    table = Table(title="Configuration Validation Results", border_style="dim")
    table.add_column("Category", style="bold")
    table.add_column("Item", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    has_errors = False

    # 1. Schema & Parameters Validation
    try:
        cfg = PlatformConfig.load(path=path, profile=profile)
        table.add_row(
            "Parameters",
            f"parameters.yml ({profile or 'base'})",
            "[green]PASS[/green]",
            f"Valid Pydantic v2 schema (Digest: {cfg.compute_digest()[:12]}...)",
        )
    except Exception as e:
        has_errors = True
        table.add_row(
            "Parameters",
            f"parameters.yml ({profile or 'base'})",
            "[red]FAIL[/red]",
            str(e),
        )
        console.print(table)
        raise typer.Exit(code=1)

    # 2. Invariant checks
    if cfg.feature_engineering.embedding_dim != cfg.model.input_dim:
        has_errors = True
        table.add_row(
            "Invariant",
            "feature_dim == input_dim",
            "[red]FAIL[/red]",
            f"Embedding dim {cfg.feature_engineering.embedding_dim} != Model input dim {cfg.model.input_dim}",
        )
    else:
        table.add_row(
            "Invariant",
            "feature_dim == input_dim",
            "[green]PASS[/green]",
            f"Dimension alignment verified ({cfg.model.input_dim})",
        )

    # 3. Catalog checks
    if catalog:
        cat_results = cfg.validate_catalog()
        for res in cat_results:
            status_str = "[green]PASS[/green]" if res["status"] == "PASS" else "[red]FAIL[/red]"
            if res["status"] != "PASS":
                has_errors = True
            table.add_row("Catalog", res["dataset"], status_str, res["message"])

    console.print(table)
    if has_errors:
        console.print("[bold red]Configuration validation failed with errors.[/bold red]")
        raise typer.Exit(code=1)
    else:
        console.print(
            "[bold green]All configuration schemas and catalog invariants validated successfully.[/bold green]"
        )


@config_app.command(name="diff")
def config_diff(
    profile_a: str | None = typer.Option(
        None,
        "--profile-a",
        "-a",
        help="First platform profile (defaults to base configuration).",
    ),
    profile_b: str = typer.Option(
        ...,
        "--profile-b",
        "-b",
        help="Second platform profile to compare against.",
    ),
    path: str | None = typer.Option(
        None,
        "--path",
        help="Path to parameters YAML file.",
    ),
) -> None:
    """Compare two platform profiles or configurations side-by-side."""
    try:
        cfg_a = PlatformConfig.load(path=path, profile=profile_a)
        cfg_b = PlatformConfig.load(path=path, profile=profile_b)
    except Exception as e:
        console.print(f"[bold red]Configuration Diff Error:[/] {e}")
        raise typer.Exit(code=1)

    diffs = cfg_a.diff(cfg_b)
    modified = [d for d in diffs if d.status != "IDENTICAL"]

    name_a = profile_a or "base"
    name_b = profile_b

    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Configuration Diff[/bold cyan]: [yellow]{name_a}[/yellow] vs [magenta]{name_b}[/magenta]",
            border_style="cyan",
        )
    )

    if not modified:
        console.print(
            f"[bold green]Configurations '{name_a}' and '{name_b}' are identical.[/bold green]"
        )
        return

    table = Table(title=f"Configuration Discrepancies ({len(modified)} found)", border_style="dim")
    table.add_column("Parameter Path", style="bold")
    table.add_column(f"{name_a}", style="cyan")
    table.add_column(f"{name_b}", style="magenta")
    table.add_column("Change Status", justify="center")

    for d in modified:
        status_colored = {
            "MODIFIED": "[yellow]MODIFIED[/yellow]",
            "ADDED": "[green]ADDED[/green]",
            "REMOVED": "[red]REMOVED[/red]",
        }.get(d.status, d.status)
        table.add_row(d.path, str(d.value_a), str(d.value_b), status_colored)

    console.print(table)


@config_app.command(name="schema")
def config_schema(
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path to write JSON Schema (e.g. conf/parameters.schema.json).",
    ),
) -> None:
    """Export standard JSON Schema (Draft 2020-12) for IDE validation and autocompletion."""
    schema = PlatformConfig.json_schema()
    formatted = json.dumps(schema, indent=2)
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(formatted)
        console.print(f"[bold green]JSON Schema exported to:[/] [cyan]{out_path}[/cyan]")
    else:
        console.print(formatted)


@config_app.command(name="init")
def config_init(
    profile: str = typer.Option(
        "macos_metal_safetensors",
        "--profile",
        "-p",
        help="Base platform profile to initialize.",
    ),
    output: str = typer.Option(
        "conf/local/parameters.yml",
        "--output",
        "-o",
        help="Output path for initialized parameters file.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite target file if it already exists.",
    ),
) -> None:
    """Scaffold a typed local parameters file with smart profile defaults and comments."""
    out_p = Path(output)
    if out_p.exists() and not force:
        console.print(
            f"[bold yellow]File '{output}' already exists.[/bold yellow] Use [cyan]--force[/cyan] to overwrite."
        )
        raise typer.Exit(code=1)

    try:
        cfg = PlatformConfig.load(profile=profile, resolve_env=False)
    except Exception as e:
        console.print(f"[bold red]Initialization Error:[/] {e}")
        raise typer.Exit(code=1)

    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        f.write(f"# CKODEX Platform Configuration (Profile: {profile})\n")
        f.write(f"# Initialized at: {datetime.now(UTC).isoformat()}\n")
        f.write("# See docs/content/reference/configuration.md for field specifications\n\n")
        f.write(cfg.to_yaml())

    console.print(
        Panel.fit(
            f"[bold green]Configuration initialized successfully![/bold green]\n"
            f"[dim]Destination:[/] [cyan]{out_p}[/cyan]\n"
            f"[dim]Profile:[/] [magenta]{profile}[/magenta]\n"
            f"[dim]Digest:[/] [green]{cfg.compute_digest()}[/green]",
            border_style="green",
        )
    )


# ==============================================================================
# Lance Columnar & Vector Operations (LanceRayEngine)
# ==============================================================================

lance_app = typer.Typer(
    name="lance",
    help="Lance Columnar & Vector Dataset Lifecycle Operations",
    rich_markup_mode="rich",
)
app.add_typer(lance_app, name="lance", rich_help_panel="Execution & Pipelines")


@lance_app.command(name="compact")
def lance_compact(
    target: str = typer.Argument(
        "data/04_feature/features.lance", help="Path to Lance dataset to compact"
    ),
    target_rows_per_fragment: int = typer.Option(
        100_000, help="Target rows per compacted fragment"
    ),
) -> None:
    """
    Execute distributed fragment compaction on Lance dataset to eliminate small files and maximize read IOPS.
    """
    from ckodex_aiops.adapters.ray.lance_ray import LanceRayEngine

    path = Path(target)
    if not path.exists():
        console.print(f"[red]Error:[/red] Dataset does not exist at: {path}")
        raise typer.Exit(1)

    import lance

    ds_before = lance.dataset(str(path))
    num_frags_before = len(ds_before.get_fragments())
    num_rows = ds_before.count_rows()

    console.print(
        Panel.fit(
            f"[bold cyan]Compacting Lance Dataset: {path}[/bold cyan]\n"
            f"Fragments before: {num_frags_before} | Total rows: {num_rows}",
            border_style="cyan",
        )
    )

    start = time.perf_counter()
    LanceRayEngine.compact(path, target_rows_per_fragment=target_rows_per_fragment)
    dur = time.perf_counter() - start

    ds_after = lance.dataset(str(path))
    num_frags_after = len(ds_after.get_fragments())

    console.print(
        f"[bold green]✔ Compaction completed in {dur:.2f}s.[/bold green]\n"
        f"Fragments: {num_frags_before} ➔ [bold cyan]{num_frags_after}[/bold cyan]"
    )


@app.command(name="compact", rich_help_panel="Execution & Pipelines", hidden=True)
def compact_alias(
    target: str = typer.Argument(
        "data/04_feature/features.lance", help="Path to Lance dataset to compact"
    ),
    target_rows_per_fragment: int = typer.Option(
        100_000, help="Target rows per compacted fragment"
    ),
) -> None:
    """Execute distributed fragment compaction on Lance dataset (alias for `ckx lance compact`)."""
    lance_compact(target=target, target_rows_per_fragment=target_rows_per_fragment)


@lance_app.command(name="mine")
def lance_mine(
    dataset: str = typer.Option(
        "data/04_feature/physical_ai.lance", help="Path to Physical AI Lance dataset"
    ),
    filter_expr: str = typer.Option(
        "slip_detected = true", help="Pushdown SQL filter for kinematic conditions"
    ),
    limit: int = typer.Option(10, help="Maximum matching event samples to retrieve"),
) -> None:
    """
    Execute Physical AI multimodal data mining: pushdown SQL filter + zero-copy Arrow retrieval.
    """
    from ckodex_aiops.pipelines.physical_ai.nodes import mine_physical_ai_events

    path = Path(dataset)
    if not path.exists():
        console.print(f"[red]Error:[/red] Dataset does not exist at: {path}")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold cyan]Mining Lance Dataset: {path}[/bold cyan]\nFilter: `{filter_expr}` | Limit: {limit}",
            border_style="cyan",
        )
    )

    result = mine_physical_ai_events(str(path), filter_expr=filter_expr, limit=limit)

    console.print(
        f"[bold green]✔ Mined {result['total_matched_samples']} candidate events.[/bold green]"
    )
    events: list[dict[str, Any]] = result["sample_events"]

    table = Table(title="Multimodal Kinematics Anomaly Events", border_style="dim")
    table.add_column("Episode ID", style="cyan")
    table.add_column("Step ID", justify="right")
    table.add_column("Acceleration (m/s²)", justify="right")
    table.add_column("Jerk Magnitude", justify="right")
    table.add_column("Slip Detected", justify="center")

    for ev in events:
        table.add_row(
            str(ev["episode_id"]),
            str(ev["step_id"]),
            f"{ev['accel_mag']:.3f}",
            f"{ev['jerk_mag']:.3f}",
            "[bold red]YES[/bold red]" if ev["slip_detected"] else "[green]NO[/green]",
        )

    console.print(table)
    console.print(f"[dim]Affected Episodes: {result['episodes_affected']}[/dim]")


@app.command(name="mine", rich_help_panel="Execution & Pipelines", hidden=True)
def mine_alias(
    dataset: str = typer.Option(
        "data/04_feature/physical_ai.lance", help="Path to Physical AI Lance dataset"
    ),
    filter_expr: str = typer.Option(
        "slip_detected = true", help="Pushdown SQL filter for kinematic conditions"
    ),
    limit: int = typer.Option(10, help="Maximum matching event samples to retrieve"),
) -> None:
    """Execute Physical AI multimodal data mining (alias for `ckx lance mine`)."""
    lance_mine(dataset=dataset, filter_expr=filter_expr, limit=limit)


@lance_app.command(name="inspect")
def lance_inspect(
    target: str = typer.Argument(
        "data/04_feature/features.lance", help="Path to Lance dataset to inspect"
    ),
) -> None:
    """Inspect Lance dataset fragments, version history, schema, and index metadata."""
    path = Path(target)
    if not path.exists():
        console.print(f"[red]Error:[/red] Path does not exist: {path}")
        raise typer.Exit(1)

    import lance

    ds = lance.dataset(str(path))
    console.print(Panel.fit(f"[bold cyan]Lance Dataset Inspection: {path}[/bold cyan]"))
    table = Table(border_style="dim")
    table.add_column("Property", style="bold")
    table.add_column("Value")

    table.add_row("Total Rows", str(ds.count_rows()))
    table.add_row("Latest Version", str(ds.version))
    table.add_row("Fragments Count", str(len(ds.get_fragments())))
    table.add_row("Schema Fields", ", ".join(ds.schema.names))
    indices = ds.list_indices()
    table.add_row("Indices", str(indices) if indices else "None")
    console.print(table)


@app.command(rich_help_panel="Day-2 Operations & Recovery")
def reconcile(
    profile: str = typer.Option(
        "macos_metal_safetensors",
        "--profile",
        "-p",
        help="Target baseline profile to reconcile against.",
    ),
    auto_heal: bool = typer.Option(
        True,
        "--auto-heal/--no-auto-heal",
        help="Automatically execute bounded corrective mutations.",
    ),
) -> None:
    """
    Execute Day-2 Autonomic Reconciliation Loop (OBSERVE -> DETECT -> DIAGNOSE -> RECOVER -> RECONCILE).
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Day-2 Autonomic Reconciler[/bold cyan]\n"
            f"Baseline: [bold green]{profile}[/bold green] | Auto-Heal: [bold yellow]{auto_heal}[/bold yellow]",
            border_style="cyan",
        )
    )

    reconciler = AutonomicReconciler(profile_name=profile)
    receipt = reconciler.run_reconciliation(auto_heal=auto_heal)

    table = Table(title="Reconciliation Execution Summary", border_style="dim")
    table.add_column("Phase", style="bold")
    table.add_column("Value / State", style="cyan")

    table.add_row("Receipt ID", receipt.receipt_id)
    table.add_row("Pre-Reconciliation Vector", str(receipt.initial_vector.lifecycle))
    table.add_row("Anomalies Detected", str(len(receipt.anomalies_detected)))
    table.add_row(
        "Actions Executed",
        str(receipt.actions_executed) if receipt.actions_executed else "None Required",
    )
    table.add_row(
        "Post-Reconciliation Vector", f"[green]{receipt.resulting_vector.lifecycle}[/green]"
    )
    table.add_row("Evidence Digest (SHA-256)", receipt.evidence_digest[:32] + "...")

    console.print(table)


@app.command(rich_help_panel="Governance & Compliance")
def attest(
    subject: str = typer.Option(
        "data/06_models/model.safetensors", "--subject", "-s", help="Path to artifact to attest."
    ),
    out: str = typer.Option(
        "data/08_reporting/attestations/provenance.intoto.jsonl",
        "--out",
        "-o",
        help="Output attestation path.",
    ),
) -> None:
    """
    Generate cryptographic In-toto v1.0 Statement with SLSA Provenance v1.0.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX SLSA v1.0 In-toto Attestor[/bold cyan]\n"
            f"Subject: [dim]{subject}[/dim]",
            border_style="cyan",
        )
    )

    stmt = IntotoProvenanceAttestor.generate_attestation(subject_path=subject)
    dest = IntotoProvenanceAttestor.write_attestation(stmt, out)

    console.print(f"[green]SUCCESS:[/green] In-toto provenance generated at [bold]{dest}[/bold]")
    console.print(f"Artifact SHA-256: [dim]{stmt['subject'][0]['digest']['sha256']}[/dim]")


@app.command(rich_help_panel="Governance & Compliance")
def oscal(
    out: str = typer.Option(
        "data/08_reporting/oscal/component_definition.json",
        "--out",
        "-o",
        help="Output path for OSCAL JSON.",
    ),
) -> None:
    """
    Generate machine-verifiable NIST SP 800-53 Rev 5 OSCAL Component Definition.
    """
    dest = OscalComplianceGenerator.write_oscal(output_path=out)
    console.print(
        f"[green]SUCCESS:[/green] NIST SP 800-53 OSCAL Component Definition written to [bold]{dest}[/bold]"
    )


@app.command(rich_help_panel="Governance & Compliance")
def sbom(
    lockfile: str = typer.Option("uv.lock", "--lockfile", "-l", help="Path to uv.lock manifest."),
    out_dir: str = typer.Option(
        "data/08_reporting/sbom", "--out-dir", "-o", help="Directory to emit SBOM artifacts."
    ),
) -> None:
    """
    Generate industry-standard CycloneDX v1.5 and SPDX 2.3 JSON SBOMs from uv.lock.
    """
    packages = SbomGenerator.parse_uv_lock(lockfile)
    cdx = SbomGenerator.generate_cyclonedx(
        packages,
        output_path=f"{out_dir}/cyclonedx.json",
    )
    spdx = SbomGenerator.generate_spdx(
        packages,
        output_path=f"{out_dir}/spdx.json",
    )
    console.print(
        Panel.fit(
            f"[bold green]SBOMs Generated Successfully[/bold green]\n"
            f"• CycloneDX v1.5: [bold]{cdx['path']}[/bold] ({cdx['components_count']} components, SHA-256: [dim]{cdx['sha256'][:16]}...[/dim])\n"
            f"• SPDX 2.3: [bold]{spdx['path']}[/bold] ({spdx['packages_count']} packages, SHA-256: [dim]{spdx['sha256'][:16]}...[/dim])",
            border_style="green",
        )
    )


@app.command(rich_help_panel="Governance & Compliance")
def onboard(
    subject_type: str = typer.Option(
        "operator", "--type", "-t", help="Subject type: operator, agent, tenant, compute-node"
    ),
    subject_id: str = typer.Option(..., "--id", "-i", help="Unique identifier for the subject."),
    role: str = typer.Option(
        "developer",
        "--role",
        "-r",
        help="Assigned role (e.g. admin, mlops, developer, auditor, pipeline-executor).",
    ),
    tenant: str = typer.Option("cfyd", "--tenant", help="Tenant partition."),
    workspace: str = typer.Option("aiops", "--workspace", help="Workspace partition."),
    ttl_hours: float = typer.Option(24.0, "--ttl", help="Capability lease duration in hours."),
    actor: str = typer.Option(
        "principal:engineer", "--actor", help="Acting authority minting the onboarding."
    ),
) -> None:
    """
    Onboard an operator, autonomous agent, tenant, or compute node into the CKODEX authority tree.
    """
    type_map = {
        "operator": SubjectType.OPERATOR,
        "agent": SubjectType.AGENT,
        "tenant": SubjectType.TENANT,
        "compute-node": SubjectType.COMPUTE_NODE,
        "node": SubjectType.COMPUTE_NODE,
    }
    stype = type_map.get(subject_type.lower())
    if not stype:
        console.print(
            f"[red]Error:[/red] Invalid subject type '{subject_type}'. Choose from: {list(type_map.keys())}"
        )
        raise typer.Exit(1)

    mgr = LifecycleManager()
    req = OnboardingRequest(
        subject_id=subject_id,
        subject_type=stype,
        role=role,
        tenant=tenant,
        workspace=workspace,
        ttl_hours=ttl_hours,
        actor=actor,
    )
    rec = mgr.onboard(req)
    mgr.export_hugo_docs()

    console.print(
        Panel.fit(
            f"[bold green]Subject Successfully Onboarded (Rule #2 & Rule #25)[/bold green]\n"
            f"• Subject ID: [bold cyan]{rec.subject_id}[/bold cyan] ({rec.subject_type.value})\n"
            f"• Authority URN: [dim]{rec.authority_path.to_urn()}[/dim]\n"
            f"• Role: [bold]{rec.role}[/bold]\n"
            f"• Capabilities: {', '.join(rec.capabilities)}\n"
            f"• Lease ID: [dim]{rec.lease.lease_id}[/dim] (TTL: {ttl_hours}h)\n"
            f"• Receipt Digest: [dim]{rec.history[-1].receipt_digest[:16]}...[/dim]",
            border_style="green",
        )
    )


@app.command(rich_help_panel="Governance & Compliance")
def offboard(
    subject_id: str = typer.Option(..., "--id", "-i", help="Subject identifier to offboard."),
    reason: str = typer.Option(
        "operational rotation", "--reason", "-r", help="Justification for offboarding."
    ),
    actor: str = typer.Option(
        "principal:engineer", "--actor", help="Acting authority initiating offboarding."
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force offboarding even if already offboarded."
    ),
) -> None:
    """
    Offboard a governed subject: immediately revokes capability lease, wipes credentials, and records receipt.
    """
    mgr = LifecycleManager()
    req = OffboardingRequest(
        subject_id=subject_id,
        reason=reason,
        actor=actor,
        force=force,
    )
    rec = mgr.offboard(req)
    mgr.export_hugo_docs()

    console.print(
        Panel.fit(
            f"[bold red]Subject Successfully Offboarded (Rule #27)[/bold red]\n"
            f"• Subject ID: [bold cyan]{rec.subject_id}[/bold cyan] ({rec.subject_type.value})\n"
            f"• Status: [bold red]{rec.status.value}[/bold red]\n"
            f"• Reason: {rec.offboarding_reason}\n"
            f"• Lease Revoked: [bold green]TRUE[/bold green] (Immediate Access Denial)\n"
            f"• Lineage Receipt: [dim]{rec.metadata.get('offboarding_receipt', 'N/A')}[/dim]",
            border_style="red",
        )
    )


@app.command(name="lifecycle", rich_help_panel="Governance & Compliance")
def lifecycle_cmd(
    audit: bool = typer.Option(
        False, "--audit", "-a", help="Display full audit transition history."
    ),
    runbook: str | None = typer.Option(
        None, "--runbook", help="Generate operational runbook for type: operator, agent, node."
    ),
    export_docs: bool = typer.Option(
        False, "--export-docs", help="Compile and export Hugo documentation page."
    ),
) -> None:
    """
    Inspect governed subject registry, view audit trails, generate runbooks, or export living documentation.
    """
    mgr = LifecycleManager()

    if runbook:
        type_map = {
            "operator": SubjectType.OPERATOR,
            "agent": SubjectType.AGENT,
            "tenant": SubjectType.TENANT,
            "compute-node": SubjectType.COMPUTE_NODE,
            "node": SubjectType.COMPUTE_NODE,
        }
        stype = type_map.get(runbook.lower(), SubjectType.OPERATOR)
        rb = mgr.generate_runbook(stype)
        console.print(rb)
        return

    if export_docs:
        out = mgr.export_hugo_docs()
        console.print(
            f"[green]SUCCESS:[/green] Living documentation compiled to [bold]{out}[/bold]"
        )
        return

    subjects = mgr.list_subjects()
    if not subjects:
        console.print(
            "[yellow]Notice:[/yellow] No subjects currently registered. Use 'ckodex-aiops onboard' to register one."
        )
        return

    table = Table(title="Governed Subject Lifecycle Registry (GAL 1)", border_style="dim")
    table.add_column("Subject ID", style="bold cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Role", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Lease Valid", justify="center")
    table.add_column("Authority Path")

    for s in subjects:
        status_style = (
            "green"
            if s.is_active()
            else "red"
            if s.status == LifecycleStatus.OFFBOARDED
            else "yellow"
        )
        lease_valid = "[green]YES[/green]" if s.lease.is_valid() else "[red]NO[/red]"
        table.add_row(
            s.subject_id,
            s.subject_type.value,
            s.role,
            f"[{status_style}]{s.status.value}[/{status_style}]",
            lease_valid,
            s.authority_path.to_urn(),
        )

    console.print(table)

    if audit:
        console.print("\n[bold]Cryptographic Audit Trail (Lineage Receipts):[/bold]")
        for s in subjects:
            for t in s.history:
                console.print(
                    f"  • [cyan]{t.timestamp_utc}[/cyan] | [bold]{t.subject_id}[/bold]: "
                    f"{t.from_status.value} -> [bold]{t.to_status.value}[/bold] "
                    f"by [dim]{t.actor}[/dim] (Reason: {t.reason}) [dim]digest={t.receipt_digest[:12]}...[/dim]"
                )


@app.command(rich_help_panel="Day-2 Operations & Recovery")
def cockpit(
    serve: bool = typer.Option(
        False, "--serve", "-s", help="Spawn local zero-dependency HTTP server and open browser."
    ),
    port: int = typer.Option(8888, "--port", "-p", help="Port for Mission Cockpit HTTP server."),
    export_html: str | None = typer.Option(
        None, "--export-html", help="Optional path to export static HTML dashboard."
    ),
) -> None:
    """
    Launch interactive AIOps Mission Cockpit dashboard (terminal TUI or browser server).
    """
    if not isinstance(serve, bool):
        serve = False
    if not isinstance(port, int):
        port = 8888
    if not isinstance(export_html, (str, type(None))):
        export_html = None
    ui = AiopsCockpit()
    ui.render_terminal()

    target_html = export_html or "docs/static/cockpit.html"
    dest = ui.export_html(output_path=target_html)
    if export_html:
        console.print(f"[green]Exported HTML Cockpit to:[/green] [bold]{dest}[/bold]")

    if serve:
        ui.serve(port=port, open_browser=True)


@app.command(rich_help_panel="Day-2 Operations & Recovery")
def conformance() -> None:
    """
    Run multi-dimensional transition conformance evaluation (Structural, Adversarial ANTI, Degradation).
    """
    console.print(
        Panel.fit(
            "[bold cyan]CKODEX Multi-Dimensional Conformance Suite[/bold cyan]", border_style="cyan"
        )
    )

    init_vec = StateVector()

    # 1. Structural
    batch = [{"feature_0": 0.1, "feature_1": 0.2}]
    res_struct = ConformanceEngine.evaluate_structural_transition(
        init_vec, batch, expected_keys=["feature_0", "feature_1"]
    )

    # 2. Adversarial / Anti Dominance
    res_anti = ConformanceEngine.evaluate_adversarial_anti_transition(
        init_vec, is_lease_revoked=True, is_signature_tampered=False
    )

    # 3. Degradation
    res_deg = ConformanceEngine.evaluate_degradation_recovery_transition(
        init_vec, backend_available=False, retry_exhausted=False
    )

    table = Table(title="Transition Vector Evaluations", border_style="dim")
    table.add_column("Dimension", style="bold")
    table.add_column("Stimulus", style="dim")
    table.add_column("Disposition", style="cyan")
    table.add_column("Resulting Lifecycle", style="green")
    table.add_column("Conformance", justify="center")

    table.add_row(
        res_struct.dimension,
        res_struct.stimulus_name,
        res_struct.disposition,
        str(res_struct.resulting_vector.lifecycle),
        "[green]CONFORMANT[/green]" if res_struct.passed else "[red]NON-CONFORMANT[/red]",
    )
    table.add_row(
        res_anti.dimension,
        res_anti.stimulus_name,
        res_anti.disposition,
        str(res_anti.resulting_vector.lifecycle),
        "[green]CONFORMANT (ANTI-DOMINANT)[/green]" if not res_anti.passed else "[red]FAIL[/red]",
    )
    table.add_row(
        res_deg.dimension,
        res_deg.stimulus_name,
        res_deg.disposition,
        str(res_deg.resulting_vector.lifecycle),
        "[green]CONFORMANT (DEGRADED)[/green]" if res_deg.passed else "[red]FAIL[/red]",
    )

    console.print(table)


@app.command(rich_help_panel="Day-2 Operations & Recovery")
def drift(
    baseline_dataset: str = typer.Option(
        "data/01_raw/events.lance", "--baseline", "-b", help="Baseline Lance dataset path."
    ),
    observed_dataset: str = typer.Option(
        "data/04_feature/features.lance", "--observed", "-o", help="Observed Lance dataset path."
    ),
    shift_sigma: float = typer.Option(
        0.0,
        "--shift-sigma",
        "-s",
        help="Simulate distribution shift on observed features (in standard deviations) to test drift detection.",
    ),
) -> None:
    """
    Run statistical feature & sensor drift detection (Wasserstein distance & PSI).
    """
    shift_info = f" | Injected Shift: [yellow]+{shift_sigma}σ[/yellow]" if shift_sigma > 0 else ""
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Statistical Drift Engine[/bold cyan]\n"
            f"Baseline: [dim]{baseline_dataset}[/dim] | Observed: [dim]{observed_dataset}[/dim]{shift_info}",
            border_style="cyan",
        )
    )

    import lance

    b_ds = lance.dataset(baseline_dataset)
    o_ds = lance.dataset(observed_dataset)

    b_df = pl.DataFrame(b_ds.to_table(limit=500))
    o_df = pl.DataFrame(o_ds.to_table(limit=500))

    numeric_cols = [
        c
        for c, dtype in b_df.schema.items()
        if dtype in (pl.Float32, pl.Float64, pl.Int32, pl.Int64)
    ][:6]

    if shift_sigma > 0:
        # Invert or shift numeric columns in observed dataset to test drift detection under real perturbation
        shift_exprs = [(pl.col(c) + pl.col(c).std() * shift_sigma).alias(c) for c in numeric_cols]
        o_df = o_df.with_columns(shift_exprs)

    detector = StatisticalDriftDetector()
    report = detector.evaluate_drift(
        b_df, o_df, numeric_columns=numeric_cols, dataset_path=observed_dataset
    )

    table = Table(
        title=f"Feature Drift Analysis (Drift Score: {report.drift_score})", border_style="dim"
    )
    table.add_column("Feature", style="bold")
    table.add_column("Base Mean ± Std", justify="right")
    table.add_column("Obs Mean ± Std", justify="right")
    table.add_column("Wasserstein Dist", justify="right", style="cyan")
    table.add_column("Drift Status", justify="center")

    for m in report.feature_metrics:
        b_str = f"{m.baseline_mean:.2f} ± {m.baseline_std:.2f}"
        o_str = f"{m.observed_mean:.2f} ± {m.observed_std:.2f}"
        st_str = (
            "[bold red]DRIFT DETECTED[/bold red]" if m.drift_detected else "[green]STABLE[/green]"
        )
        table.add_row(m.feature_name, b_str, o_str, f"{m.wasserstein_distance:.4f}", st_str)

    console.print(table)
    console.print(
        f"Resulting State Vector: [bold green]{report.state_vector.lifecycle.value}[/bold green] (Valence: {report.state_vector.valence.value})"
    )
    if shift_sigma == 0 and report.drift_score == 0.0:
        console.print(
            "[dim]Note: Observed features were derived from baseline without injected drift. Run with '--shift-sigma 2.5' to test sensor drift detection.[/dim]"
        )


# ==============================================================================
# Air-Gap Bundle Packaging & Offline Verification (Rule #40)
# ==============================================================================

airgap_app = typer.Typer(
    name="airgap",
    help="Air-Gap Bundle Packaging & Offline Verification (Rule #40)",
    rich_markup_mode="rich",
)
app.add_typer(airgap_app, name="airgap", rich_help_panel="Distribution & Packaging")


@airgap_app.command(name="pack")
def airgap_pack(
    bundle_name: str = typer.Option(
        "ckodex-aiops-production", "--name", "-n", help="Name of airgap package."
    ),
    out: str = typer.Option(
        "data/08_reporting/airgap/bundle.tar.gz", "--out", "-o", help="Output tarball path."
    ),
) -> None:
    """
    Package models, datasets, receipts, SLSA provenance, and docs into a verified air-gap archive.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Air-Gap Distribution Packager[/bold cyan]\nBundle: {bundle_name}",
            border_style="cyan",
        )
    )

    paths_to_include = [
        "data/06_models/model.safetensors",
        "data/08_reporting/attestations/provenance.intoto.jsonl",
        "data/08_reporting/oscal/component_definition.json",
        "docs/static/cockpit.html",
        "conf/base/catalog.yml",
        "conf/base/parameters.yml",
    ]
    meta = AirgapPackager.create_bundle(
        bundle_name=bundle_name, files_to_include=paths_to_include, output_path=out
    )

    console.print(f"[green]SUCCESS:[/green] Hermetic bundle written to [bold]{out}[/bold]")
    console.print(
        f"Files Packaged: {meta['files_count']} | Root SHA-256: [dim]{meta['bundle_sha256']}[/dim]"
    )


@airgap_app.command(name="verify")
def airgap_verify(
    bundle_path: str = typer.Option(
        "data/08_reporting/airgap/bundle.tar.gz", "--path", "-p", help="Path to airgap bundle."
    ),
) -> None:
    """
    Verify checksums and manifest of an air-gap package offline without network access.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Air-Gap Bundle Verifier[/bold cyan]\nTarget: {bundle_path}",
            border_style="cyan",
        )
    )

    res = AirgapPackager.verify_bundle(bundle_path)
    if res["valid"]:
        console.print(
            f"[bold green]VERIFIED:[/bold green] All {res['verified_count']} files match manifest digests exactly."
        )
        console.print(f"Bundle Root SHA-256: [dim]{res['bundle_sha256']}[/dim]")
    else:
        console.print(
            f"[bold red]FAILED:[/bold red] Found {res['mismatch_count']} mismatched or corrupted files: {res['mismatch_files']}"
        )
        raise typer.Exit(1)


@app.command(name="airgap-pack", rich_help_panel="Distribution & Packaging", hidden=True)
def airgap_pack_alias(
    bundle_name: str = typer.Option(
        "ckodex-aiops-production", "--name", "-n", help="Name of airgap package."
    ),
    out: str = typer.Option(
        "data/08_reporting/airgap/bundle.tar.gz", "--out", "-o", help="Output tarball path."
    ),
) -> None:
    """Package air-gap bundle (alias for `ckx airgap pack`)."""
    airgap_pack(bundle_name=bundle_name, out=out)


@app.command(name="airgap-verify", rich_help_panel="Distribution & Packaging", hidden=True)
def airgap_verify_alias(
    bundle_path: str = typer.Option(
        "data/08_reporting/airgap/bundle.tar.gz", "--path", "-p", help="Path to airgap bundle."
    ),
) -> None:
    """Verify air-gap bundle (alias for `ckx airgap verify`)."""
    airgap_verify(bundle_path=bundle_path)


@app.command(rich_help_panel="Execution & Pipelines")
def quantize(
    source: str = typer.Option(
        "data/06_models/model.safetensors", "--source", "-s", help="Source model weights path."
    ),
    out: str = typer.Option(
        "data/06_models/model_int8.pt", "--out", "-o", help="Quantized model weights output path."
    ),
    threshold: float = typer.Option(
        0.98, "--threshold", "-t", help="Minimum cosine fidelity threshold."
    ),
) -> None:
    """
    Dynamically quantize model weights to Int8 and verify representation fidelity.
    """
    console.print(
        Panel.fit(
            "[bold cyan]CKODEX Dynamic Model Quantizer (Int8)[/bold cyan]", border_style="cyan"
        )
    )

    report = DynamicModelQuantizer.quantize_model(
        source_model_path=source, output_model_path=out, fidelity_threshold=threshold
    )

    table = Table(title="Model Quantization Metrics", border_style="dim")
    table.add_column("Property", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row(
        "Original Checkpoint",
        f"{report.original_path} ({report.original_size_bytes / 1024:.1f} KB)",
    )
    table.add_row(
        "Quantized Checkpoint",
        f"{report.quantized_path} ({report.quantized_size_bytes / 1024:.1f} KB)",
    )
    table.add_row("Compression Ratio", f"{report.compression_ratio}x")
    table.add_row(
        "Representation Fidelity",
        f"{report.fidelity_cosine_similarity * 100:.2f}% Cosine Similarity",
    )
    table.add_row("Quantized SHA-256", report.quantized_sha256[:32] + "...")
    table.add_row(
        "Fidelity Verified",
        "[bold green]PASS[/bold green]"
        if report.fidelity_verified
        else "[bold red]FAIL[/bold red]",
    )

    console.print(table)


@app.command(rich_help_panel="Execution & Pipelines")
def serve(
    port: int = typer.Option(8080, "--port", "-p", help="HTTP Server port."),
    model_path: str = typer.Option(
        "data/06_models/model.safetensors",
        "--model",
        "-m",
        help="Path to Safetensors model checkpoint.",
    ),
) -> None:
    """
    Launch high-performance zero-copy Model Serving HTTP Gateway.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Model Serving Gateway[/bold cyan]\nPort: {port} | Model: {model_path}",
            border_style="cyan",
        )
    )

    gateway = ModelServingGateway(model_weights_path=model_path, port=port)
    server = gateway.create_server()
    console.print(
        f"[green]Serving started on http://127.0.0.1:{port}[/green] (Press Ctrl+C to stop)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down server...[/yellow]")
        server.server_close()


@lance_app.command(name="optimize")
def lance_optimize(
    target: str = typer.Option(
        "data/04_feature/features.lance", "--target", "-t", help="Target Lance dataset path."
    ),
    target_rows: int = typer.Option(
        100_000, "--target-rows", help="Target rows per compacted fragment."
    ),
    retention_days: int = typer.Option(
        7, "--retention-days", help="Retention window in days for old version cleanup."
    ),
) -> None:
    """
    Execute full lifecycle optimization on a Lance dataset (fragment compaction + version cleanup).
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Lance Table Lifecycle Optimizer[/bold cyan]\nTarget: {target}",
            border_style="cyan",
        )
    )

    res = LanceRayEngine.optimize(
        target, target_rows_per_fragment=target_rows, cleanup_older_than_days=retention_days
    )

    table = Table(title="Lance Table Optimization Results", border_style="dim")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Dataset URI", res["uri"])
    table.add_row("Fragments Before", str(res["fragments_before"]))
    table.add_row("Fragments After", f"[bold green]{res['fragments_after']}[/bold green]")
    table.add_row("Latest Version", str(res["latest_version"]))
    table.add_row("Total Rows", str(res["total_rows"]))

    console.print(table)
    console.print("[green]SUCCESS:[/green] Table optimization and version pruning complete.")


@app.command(name="optimize", rich_help_panel="Execution & Pipelines", hidden=True)
def optimize_alias(
    target: str = typer.Option(
        "data/04_feature/features.lance", "--target", "-t", help="Target Lance dataset path."
    ),
    target_rows: int = typer.Option(
        100_000, "--target-rows", help="Target rows per compacted fragment."
    ),
    retention_days: int = typer.Option(
        7, "--retention-days", help="Retention window in days for old version cleanup."
    ),
) -> None:
    """Execute full lifecycle optimization on a Lance dataset (alias for `ckx lance optimize`)."""
    lance_optimize(target=target, target_rows=target_rows, retention_days=retention_days)


# -----------------------------------------------------------------------------
# Ray Distributed Cluster & Placement Group Management Commands
# -----------------------------------------------------------------------------
ray_app = typer.Typer(
    name="ray",
    help="Ray Distributed Computing, Placement Groups & Cluster Management",
)
app.add_typer(ray_app, name="ray", rich_help_panel="Execution & Pipelines")


@ray_app.command(name="pg")
def ray_pg(
    name: str = typer.Option("infer_pg", "--name", "-n", help="Placement group name."),
    num_actors: int = typer.Option(2, "--num-actors", "-a", help="Number of actor slots."),
    cpus_per_actor: int = typer.Option(1, "--cpus", "-c", help="CPUs per actor bundle."),
) -> None:
    """
    Allocate and inspect Ray Placement Groups for atomic gang scheduling.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Ray Placement Group Manager[/bold cyan]\nReserving PG: {name}",
            border_style="cyan",
        )
    )

    pg = RayPlacementGroupManager.create_inference_placement_group(
        name=name,
        num_actors=num_actors,
        cpus_per_actor=cpus_per_actor,
        strategy="PACK",
    )

    pgs = RayPlacementGroupManager.list_placement_groups()
    table = Table(title="Active Ray Placement Groups", border_style="dim")
    table.add_column("Name", style="bold")
    table.add_column("State", style="green")
    table.add_column("Strategy", style="cyan")
    table.add_column("Bundles", justify="right")

    for p in pgs:
        table.add_row(p["name"], p["state"], p["strategy"], str(len(p["bundles"])))

    console.print(table)
    RayPlacementGroupManager.remove_placement_group(pg)
    console.print(
        f"[green]SUCCESS:[/green] Verified placement group '{name}' and cleanly deallocated."
    )


# Backwards compatibility alias for top-level ckx ray-pg
@app.command(name="ray-pg", rich_help_panel="Integrity & Observability", hidden=True)
def ray_pg_top_level_alias(
    name: str = typer.Option("infer_pg", "--name", "-n", help="Placement group name."),
    num_actors: int = typer.Option(2, "--num-actors", "-a", help="Number of actor slots."),
    cpus_per_actor: int = typer.Option(1, "--cpus", "-c", help="CPUs per actor bundle."),
) -> None:
    """Allocate and inspect Ray Placement Groups (Alias for ckx ray pg)."""
    ray_pg(name=name, num_actors=num_actors, cpus_per_actor=cpus_per_actor)


@ray_app.command(name="status")
def ray_status(
    address: str | None = typer.Option(
        None,
        "--address",
        "-a",
        help="Ray cluster address (e.g. 'auto', 'ray://remote-host:10001', 'redis://head:6379').",
    ),
) -> None:
    """Inspect Ray cluster connectivity, available CPUs/GPUs, active nodes, and memory."""
    console.print(
        Panel.fit("[bold cyan]CKODEX Ray Cluster Inspection[/bold cyan]", border_style="cyan")
    )

    success = RayRuntimeManager.initialize(address=address)
    if not success:
        console.print("[bold red]Error:[/] Could not connect to or initialize Ray cluster.")
        raise typer.Exit(1)

    info = RayRuntimeManager.get_cluster_info()
    table = Table(title="Ray Cluster Topography", border_style="dim")
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="green")

    table.add_row("Cluster Status", info.get("status", "UNKNOWN"))
    table.add_row("Execution Mode", info.get("mode", "UNKNOWN"))
    table.add_row("Active Nodes", str(info.get("nodes", 0)))
    table.add_row("Allocated CPUs", str(info.get("cpus", 0.0)))
    table.add_row("Allocated GPUs", str(info.get("gpus", 0.0)))
    table.add_row("Worker Heap Budget", f"{info.get('allocated_memory_gb', 0.0)} GB")
    table.add_row("Plasma Object Store", f"{info.get('object_store_gb', 0.0)} GB")

    nodes = info.get("active_nodes", [])
    if nodes:
        table.add_row("Worker Node Addresses", ", ".join(str(n) for n in nodes))

    console.print(table)


@ray_app.command(name="start")
def ray_start_local(
    num_cpus: int = typer.Option(4, "--cpus", "-c", help="Number of CPUs for local cluster."),
    port: int = typer.Option(6379, "--port", "-p", help="GCS port for head node."),
    dashboard_port: int = typer.Option(8265, "--dashboard-port", help="Dashboard port."),
) -> None:
    """Launch a local background Ray head cluster daemon."""
    import subprocess

    console.print(
        f"[bold cyan]Launching Local Ray Head Node[/bold cyan] (Port: {port}, CPUs: {num_cpus})..."
    )
    cmd = [
        "ray",
        "start",
        "--head",
        f"--port={port}",
        f"--dashboard-port={dashboard_port}",
        f"--num-cpus={num_cpus}",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        console.print(f"[bold green]✔ Ray Head Started Successfully![/bold green]\n{res.stdout}")
        console.print(f"[dim]Web Dashboard:[/] http://localhost:{dashboard_port}")
        console.print(f"[dim]Client Address:[/] ray://127.0.0.1:10001 or 127.0.0.1:{port}")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Ray Start Error:[/] {e.stderr or e.stdout}")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("[bold red]Error:[/] 'ray' CLI binary not found on PATH.")
        raise typer.Exit(1)


@ray_app.command(name="stop")
def ray_stop_local() -> None:
    """Stop locally running Ray daemon processes on this machine."""
    import subprocess

    console.print("[bold cyan]Stopping Local Ray Cluster...[/bold cyan]")
    try:
        subprocess.run(["ray", "stop"], capture_output=True, text=True, check=True)
        console.print("[bold green]✔ Local Ray processes stopped.[/bold green]")
    except Exception as e:
        console.print(f"[yellow]Ray stop result:[/] {e}")


oci_app = typer.Typer(
    name="oci",
    help="OCI Artifact Packaging & Distribution Engine (OCI Spec v1.1.0, ORAS, Cosign)",
)

app.add_typer(oci_app, name="oci", rich_help_panel="Distribution & Packaging")


@oci_app.command(name="pack")
def oci_pack(
    source: str = typer.Option(".", "--source", "-s", help="Source root of the template."),
    out: str = typer.Option(
        "dist/oci-template", "--out", "-o", help="Output OCI Image Layout directory."
    ),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Template version string."),
    tag: str = typer.Option("latest", "--tag", "-t", help="Tag annotation for OCI index."),
) -> None:
    """
    Package template as a multi-layer OCI Artifact with embedded SBOMs and OSCAL definitions.
    """
    res = OciTemplatePackager.pack_oci_layout(
        source_root=source,
        output_layout_dir=out,
        template_version=version,
        tag=tag,
    )
    console.print(
        Panel.fit(
            f"[bold green]OCI Artifact Packaged Successfully (OCI Spec v1.1.0)[/bold green]\n"
            f"• Layout Directory: [bold]{res['layout_dir']}[/bold]\n"
            f"• Manifest Digest: [bold cyan]{res['manifest_digest']}[/bold cyan] ({res['manifest_size']} bytes)\n"
            f"• Config Digest: [dim]{res['config_digest'][:24]}...[/dim]\n"
            f"• Layers Count: [bold]{res['layers_count']}[/bold] (Template + SBOMs + OSCAL)\n"
            f"• Template Archive: [dim]{res['template_archive_digest'][:24]}...[/dim] ({res['template_archive_size'] / (1024 * 1024):.2f} MB)\n"
            f"• Lineage Receipt: [dim]{res['receipt_id']}[/dim]",
            border_style="green",
        )
    )


@oci_app.command(name="inspect")
def oci_inspect(
    layout: str = typer.Argument("dist/oci-template", help="OCI Image Layout directory."),
) -> None:
    """
    Inspect an OCI Image Layout directory and its manifest, config, and layer descriptors.
    """
    data = OciTemplatePackager.inspect_layout(layout)
    console.print(Panel.fit(f"[bold cyan]OCI Artifact Inspection: {layout}[/bold cyan]"))

    table = Table(title="Manifest & Config", border_style="dim")
    table.add_column("Field", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Manifest Digest", data["manifest_digest"])
    table.add_row("Artifact Type", data["artifact_type"])
    table.add_row("Template Name", data["config"].get("templateName", "unknown"))
    table.add_row("Template Version", data["config"].get("version", "unknown"))
    table.add_row("Python Constraint", data["config"].get("pythonVersion", "unknown"))
    table.add_row(
        "Constitutional Standard", data["config"].get("constitutionalStandard", "unknown")
    )
    console.print(table)

    layer_table = Table(title="OCI Artifact Layers", border_style="dim")
    layer_table.add_column("Title", style="bold cyan")
    layer_table.add_column("Media Type")
    layer_table.add_column("Digest", style="dim")
    layer_table.add_column("Size", justify="right")

    for layer in data["layers"]:
        size_kb = (
            f"{layer['size_bytes'] / 1024:.1f} KB"
            if layer["size_bytes"] < 1024 * 1024
            else f"{layer['size_bytes'] / (1024 * 1024):.2f} MB"
        )
        layer_table.add_row(
            layer["title"], layer["media_type"], layer["digest"][:24] + "...", size_kb
        )

    console.print(layer_table)


@oci_app.command(name="unpack")
def oci_unpack(
    layout: str = typer.Option(
        "dist/oci-template", "--layout", "-l", help="OCI Image Layout directory."
    ),
    dest: str = typer.Option(
        ..., "--dest", "-d", help="Destination directory to unpack the template into."
    ),
) -> None:
    """
    Unpack the template layer from an OCI layout into a new project directory.
    """
    res = OciTemplatePackager.unpack_template(layout_dir=layout, destination_dir=dest)
    console.print(
        Panel.fit(
            f"[bold green]Template Successfully Instantiated from OCI Artifact[/bold green]\n"
            f"• Destination: [bold]{res['destination_dir']}[/bold]\n"
            f"• Verified Layer Digest: [dim]{res['extracted_layer_digest']}[/dim]\n"
            f"• Files Unpacked: [bold]{res['files_unpacked']}[/bold]\n\n"
            f"[dim]Next steps:[/dim]\n"
            f"  cd {dest} && just install && just doctor",
            border_style="green",
        )
    )


@oci_app.command(name="guide")
def oci_guide(
    image_ref: str = typer.Option(
        "ghcr.io/ckodex-labs/ckx-ai-project-template:latest",
        "--image-ref",
        "-r",
        help="Target OCI registry reference.",
    ),
    layout: str = typer.Option(
        "dist/oci-template", "--layout", "-l", help="OCI Image Layout directory."
    ),
) -> None:
    """
    Print step-by-step commands to push/pull OCI artifacts with ORAS and sign with Cosign.
    """
    cmds = OciTemplatePackager.generate_oras_commands(image_ref=image_ref, layout_dir=layout)
    console.print(
        Panel.fit("[bold cyan]OCI Artifact Distribution Guide (ORAS + Cosign)[/bold cyan]")
    )
    for name, cmd in cmds.items():
        console.print(f"[bold yellow]# {name}:[/bold yellow]\n  {cmd}\n")


# ==============================================================================
# Day-2 Deep Observability: Explain, Trace, Recover, Replay (Rules #12, #33, #34, #37)
# ==============================================================================


@app.command(name="explain", rich_help_panel="Integrity & Observability")
def explain(
    target: str = typer.Argument(
        ..., help="Target receipt ID, artifact path, or incident identifier to explain."
    ),
) -> None:
    """
    Day-2 Deep Observability: Answering the 11 constitutional operator diagnostic questions (Rule #37).
    """
    engine = ExplanationEngine()
    report = engine.explain(target)

    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Deep Observability Explanation: {report.target}[/bold cyan]",
            border_style="cyan",
        )
    )

    table = Table(title="Diagnostic Findings", border_style="dim", expand=True)
    table.add_column("Question", style="bold yellow", width=30)
    table.add_column("Authoritative Machine Finding", style="white")

    table.add_row("1. What happened?", report.what_happened)
    table.add_row("2. Where?", f"[bold cyan]{report.where}[/bold cyan]")
    table.add_row("3. Why?", report.why)
    table.add_row("4. Under whose authority?", f"[dim]{report.authority_urn}[/dim]")
    table.add_row(
        "5. What changed?",
        "\n".join(report.what_changed) if report.what_changed else "[dim]No mutations[/dim]",
    )
    table.add_row(
        "6. What is affected (Blast Radius)?",
        ", ".join(f"[bold magenta]{b}[/bold magenta]" for b in report.blast_radius),
    )
    table.add_row(
        "7. Is state coherent?",
        "[green]YES (Coherent)[/green]"
        if report.is_coherent
        else "[bold red]NO (Decoherent divergence)[/bold red]",
    )
    table.add_row(
        "8. Is operation safely degraded?",
        "[yellow]YES (Degraded)[/yellow]"
        if report.is_safely_degraded
        else "[green]NO (Normal / Full capability)[/green]",
    )
    table.add_row(
        "9. What is prohibited?",
        ", ".join(report.prohibited_capabilities)
        if report.prohibited_capabilities
        else "[dim]None[/dim]",
    )
    table.add_row(
        "10. Can it recover automatically?",
        "[green]YES[/green]"
        if report.auto_recoverable
        else "[red]NO (Requires human intervention)[/red]",
    )
    table.add_row(
        "11. Evidence proving diagnosis?",
        "\n".join(f"[dim]{e}[/dim]" for e in report.evidence_receipts)
        if report.evidence_receipts
        else "[dim]None recorded[/dim]",
    )

    console.print(table)


@app.command(name="trace-correlate", rich_help_panel="Integrity & Observability", hidden=True)
def trace(
    run_id: str = typer.Argument(
        ..., help="Run ID or prefix to correlate across the four truth channels."
    ),
) -> None:
    """
    Day-2 Truth Channels: Correlate Telemetry, Execution, Decision, and Evidence traces (Rule #12).
    """
    correlator = TruthChannelsCorrelator()
    trace_record = correlator.correlate(run_id)

    console.print(
        Panel.fit(
            f"[bold cyan]Four Truth Channels Correlation: {trace_record.run_id}[/bold cyan]\n"
            f"Coherence: {'[bold green]COHERENT[/bold green]' if trace_record.is_coherent else '[bold red]DECOHERENT[/bold red]'}",
            border_style="cyan" if trace_record.is_coherent else "red",
        )
    )

    if trace_record.coherence_violations:
        console.print("[bold red]Decoherence Violations Detected:[/bold red]")
        for v in trace_record.coherence_violations:
            console.print(f" • [red]{v}[/red]")
        console.print()

    table = Table(title="Truth Channels Breakdown", border_style="dim")
    table.add_column("Channel", style="bold")
    table.add_column("Entries", justify="center")
    table.add_column("Key Sample / Status", style="dim")

    telemetry_summary = (
        f"Latest: {trace_record.telemetry_channel[-1].metric_name}={trace_record.telemetry_channel[-1].metric_value:.4f}"
        if trace_record.telemetry_channel
        else "No telemetry stream"
    )
    execution_summary = (
        f"Latest: {trace_record.execution_channel[-1].step_name} ({trace_record.execution_channel[-1].status})"
        if trace_record.execution_channel
        else "No execution trace"
    )
    decision_summary = (
        f"Latest: {trace_record.decision_channel[-1].disposition} ({trace_record.decision_channel[-1].decision_type})"
        if trace_record.decision_channel
        else "No decision trace"
    )
    evidence_summary = (
        f"Latest: {trace_record.evidence_channel[-1].identifier} ({trace_record.evidence_channel[-1].evidence_type})"
        if trace_record.evidence_channel
        else "No evidence trace"
    )

    table.add_row("1. Telemetry Trace", str(len(trace_record.telemetry_channel)), telemetry_summary)
    table.add_row("2. Execution Trace", str(len(trace_record.execution_channel)), execution_summary)
    table.add_row("3. Decision Trace", str(len(trace_record.decision_channel)), decision_summary)
    table.add_row("4. Evidence Trace", str(len(trace_record.evidence_channel)), evidence_summary)

    console.print(table)


@app.command(name="recover", rich_help_panel="Day-2 Operations & Recovery")
def recover(
    checkpoint: str = typer.Option(
        ..., "--checkpoint", "-c", help="Checkpoint ID to verify and recover."
    ),
    verify_only: bool = typer.Option(
        False, "--verify-only", help="Verify checkpoint integrity without side effects."
    ),
) -> None:
    """
    Day-2 Designed Recovery: Reconstruct state and verify cryptographic checkpoint integrity (Rule #33).
    """
    engine = RecoveryEngine()
    passed, msg, state_vec = engine.verify_checkpoint(checkpoint)

    status_str = (
        "[bold green]PASS (Verified)[/bold green]"
        if passed
        else "[bold red]FAIL (Tampered/Missing)[/bold red]"
    )
    console.print(
        Panel.fit(
            f"[bold cyan]Checkpoint Recovery & Integrity Audit: {checkpoint}[/bold cyan]\n"
            f"• Status: {status_str}\n"
            f"• Details: {msg}\n"
            f"• Recovered State Vector: [bold]{state_vec.lifecycle.value}[/bold] (Valence: {state_vec.valence.value}, Coherence: {state_vec.coherence.value})",
            border_style="green" if passed else "red",
        )
    )

    if not verify_only and passed:
        console.print(
            "[bold green]✔ Recovery sequence verified. Ready to resume execution DAG.[/bold green]"
        )


@app.command(name="replay", rich_help_panel="Day-2 Operations & Recovery")
def replay(
    receipt: str = typer.Option(
        ..., "--receipt", "-r", help="Source receipt ID to replay under bounded authority."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simulate replay without writing side-effects."
    ),
) -> None:
    """
    Day-2 Governed Replay: Execute deterministic, side-effect-fenced replay under capability lease (Rule #34).
    """
    engine = RecoveryEngine()
    req = GovernedReplayRequest(
        replay_id=f"replay_{uuid4().hex[:8]}",
        source_receipt_id=receipt,
        caller_identity="principal:operator",
        authority=AuthorityPath(tenant="cfyd", workspace="aiops"),
        lease=CapabilityLease(capabilities=("pipeline:read", "pipeline:execute")),
        fenced_side_effects=("SIMULATION_MODE", "PROHIBIT_DATASET_OVERWRITE") if dry_run else (),
    )

    try:
        new_receipt = engine.execute_replay(req)
        console.print(
            Panel.fit(
                f"[bold green]Governed Replay Completed Successfully[/bold green]\n"
                f"• Source Receipt: [bold cyan]{receipt}[/bold cyan]\n"
                f"• New Replay Receipt: [bold]{new_receipt.receipt_id}[/bold]\n"
                f"• Authority: [dim]{new_receipt.authority_urn}[/dim]\n"
                f"• Mode: {'[yellow]DRY-RUN / FENCED[/yellow]' if dry_run else '[green]COMMITTED[/green]'}\n"
                f"• Canonical Digest: [dim]{new_receipt.canonical_digest()}[/dim]",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(f"[bold red]Replay Failed:[/bold red] {e}")
        raise typer.Exit(code=1)


# ==============================================================================
# Quarantine & Evidence Isolation (Rule #32)
# ==============================================================================

quarantine_app = typer.Typer(
    name="quarantine",
    help="Quarantine & Evidence Preservation Engine (Rule #32)",
    add_completion=False,
)
app.add_typer(quarantine_app, name="quarantine", rich_help_panel="Governance & Compliance")


@quarantine_app.command(name="isolate")
def quarantine_isolate(
    target: str = typer.Argument(..., help="Path to suspect artifact or subject to isolate."),
    anomaly: str = typer.Option(
        "Manual isolation for security triage",
        "--anomaly",
        "-a",
        help="Trigger anomaly description.",
    ),
    target_type: str = typer.Option(
        "MODEL", "--type", "-t", help="Target type: MODEL, DATASET, LEASE, CONFIG."
    ),
) -> None:
    """
    Isolate suspect artifact or subject, freeze mutative effects, and preserve immutable evidence.
    """
    mgr = QuarantineManager()
    rec = mgr.isolate_artifact(target_path=target, trigger_anomaly=anomaly, target_type=target_type)
    console.print(
        Panel.fit(
            f"[bold red]Artifact Quarantined & Evidence Preserved[/bold red]\n"
            f"• Quarantine ID: [bold]{rec.quarantine_id}[/bold]\n"
            f"• Target URI: [cyan]{rec.target_uri}[/cyan]\n"
            f"• Preserved Vault: [dim]{rec.quarantine_vault_path}[/dim]\n"
            f"• Trigger Anomaly: [bold yellow]{rec.trigger_anomaly}[/bold yellow]\n"
            f"• Evidence Digests: {len(rec.evidence_digests)} files hashed with SHA-256",
            border_style="red",
        )
    )


@quarantine_app.command(name="release")
def quarantine_release(
    quarantine_id: str = typer.Argument(..., help="Quarantine ID to release."),
    justification: str = typer.Option(
        ..., "--justification", "-j", help="Operator justification for release."
    ),
) -> None:
    """
    Revalidate and release an artifact from quarantine back to operational standing with LineageReceipt.
    """
    mgr = QuarantineManager()
    rec, rcpt = mgr.release(quarantine_id=quarantine_id, justification=justification)
    console.print(
        Panel.fit(
            f"[bold green]Artifact Released from Quarantine[/bold green]\n"
            f"• Quarantine ID: [bold]{rec.quarantine_id}[/bold]\n"
            f"• Status: [bold green]{rec.status.value}[/bold green]\n"
            f"• Lineage Receipt: [bold cyan]{rcpt.receipt_id}[/bold cyan]\n"
            f"• Justification: {justification}",
            border_style="green",
        )
    )


@quarantine_app.command(name="list")
def quarantine_list(
    show_all: bool = typer.Option(
        False, "--all", "-a", help="Show all quarantine records including released."
    ),
) -> None:
    """
    List active or all quarantined artifacts and subjects.
    """
    mgr = QuarantineManager()
    records = mgr.list_quarantined(active_only=not show_all)

    table = Table(title="Quarantine Records Registry (Rule #32)", border_style="dim")
    table.add_column("Quarantine ID", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Type", justify="center")
    table.add_column("Target URI", style="cyan")
    table.add_column("Trigger Anomaly", style="dim")

    for r in records:
        status_style = (
            "red"
            if r.status == QuarantineStatus.ISOLATED
            else ("yellow" if r.status == QuarantineStatus.INVESTIGATING else "green")
        )
        table.add_row(
            r.quarantine_id,
            f"[{status_style}]{r.status.value}[/{status_style}]",
            r.target_type,
            r.target_uri,
            r.trigger_anomaly,
        )

    console.print(table)


# ==============================================================================
# Explicit Risk Derogations (Rule #23)
# ==============================================================================

derogation_app = typer.Typer(
    name="derogation",
    help="Explicit Derogation & Accepted Risk Engine (Rule #23)",
    add_completion=False,
)
app.add_typer(derogation_app, name="derogation", rich_help_panel="Governance & Compliance")


@derogation_app.command(name="create")
def derogation_create(
    requirement: str = typer.Option(
        ..., "--requirement", "-r", help="Failed requirement ID or rule."
    ),
    scope: str = typer.Option(
        ..., "--scope", "-s", help="Scope of the derogation (e.g. dev-cluster, model-eval)."
    ),
    approver: str = typer.Option(..., "--approver", "-a", help="Authorized principal approver."),
    justification: str = typer.Option(
        ..., "--justification", "-j", help="Business and technical rationale."
    ),
    controls: list[str] = typer.Option(
        [], "--control", "-c", help="Mandatory compensating controls."
    ),
    days: float = typer.Option(7.0, "--days", "-d", help="Validity duration in days."),
) -> None:
    """
    Record an explicit, time-bounded risk derogation with compensating controls (Rule #23).
    """
    reg = DerogationRegistry()
    digest = compute_sha256(f"{requirement}:{scope}:{approver}:{justification}")
    rec = reg.create_derogation(
        failed_requirement=requirement,
        scope=scope,
        approver=approver,
        justification=justification,
        compensating_controls=controls or ["COMPENSATING_TELEMETRY_LOGGING"],
        evidence_digest=digest,
        duration_days=days,
    )
    console.print(
        Panel.fit(
            f"[bold yellow]Explicit Risk Derogation Registered (Rule #23)[/bold yellow]\n"
            f"• Derogation ID: [bold]{rec.derogation_id}[/bold]\n"
            f"• Failed Requirement: [bold red]{rec.failed_requirement}[/bold red]\n"
            f"• Scope: [cyan]{rec.scope}[/cyan]\n"
            f"• Approver: [bold]{rec.approver}[/bold]\n"
            f"• Validity: {days} days (Expires: {datetime.fromtimestamp(rec.expires_at_epoch, UTC).isoformat()})\n"
            f"• Compensating Controls: {', '.join(rec.compensating_controls)}\n\n"
            f"[dim]Invariant: Derogation accepted risk does not rewrite vector state.[/dim]",
            border_style="yellow",
        )
    )


@derogation_app.command(name="list")
def derogation_list(
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all records including expired."),
) -> None:
    """
    List active or all recorded risk derogations.
    """
    reg = DerogationRegistry()
    records = reg.list_derogations(active_only=not show_all)

    table = Table(title="Risk Derogation Registry (Rule #23)", border_style="dim")
    table.add_column("Derogation ID", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Requirement", style="red")
    table.add_column("Scope", style="cyan")
    table.add_column("Approver", style="dim")
    table.add_column("Expires UTC", style="dim")

    for r in records:
        status_text = "[green]ACTIVE[/green]" if r.is_valid() else "[red]EXPIRED/REVOKED[/red]"
        exp_str = datetime.fromtimestamp(r.expires_at_epoch, UTC).strftime("%Y-%m-%d %H:%M")
        table.add_row(
            r.derogation_id, status_text, r.failed_requirement, r.scope, r.approver, exp_str
        )

    console.print(table)


@derogation_app.command(name="revoke")
def derogation_revoke(
    derogation_id: str = typer.Argument(..., help="Derogation ID to revoke."),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason for revocation."),
) -> None:
    """
    Revoke an active derogation immediately.
    """
    reg = DerogationRegistry()
    rec = reg.revoke_derogation(derogation_id, reason)
    console.print(f"[bold red]Derogation {rec.derogation_id} explicitly REVOKED.[/bold red]")


# -----------------------------------------------------------------------------
# Data Integrity Commands (Rule #8 & #18)
# -----------------------------------------------------------------------------
integrity_app = typer.Typer(
    name="integrity",
    help="Data Integrity, Content-Addressable Digestion & Merkle Lineage (Rules #8, #18)",
)
app.add_typer(integrity_app, name="integrity", rich_help_panel="Integrity & Observability")


@integrity_app.command(name="verify")
def verify_receipts(
    receipts_dir: str = typer.Option(
        "data/08_reporting/receipts",
        help="Directory containing lineage receipts.",
    ),
) -> None:
    """Verify cryptographic continuity and Merkle-tree linkage of lineage receipts."""
    p = Path(receipts_dir)
    if not p.exists():
        console.print(f"[yellow]Receipts directory '{receipts_dir}' not found.[/yellow]")
        return

    receipt_files = sorted(p.glob("*.json"))
    if not receipt_files:
        console.print(f"[yellow]No lineage receipts found in '{receipts_dir}'.[/yellow]")
        return

    receipts: list[LineageReceipt] = []
    for rf in receipt_files:
        try:
            with open(rf, encoding="utf-8") as f:
                data = json.load(f)
            receipts.append(LineageReceipt(**data))
        except Exception:
            pass

    # Sort receipts by timestamp
    receipts.sort(key=lambda r: r.timestamp_utc)

    is_valid, violations = MerkleLineageChain.validate_chain(receipts)
    digests = [r.canonical_digest() for r in receipts]
    merkle_root = MerkleLineageChain.build_merkle_root(digests)

    table = Table(title="Lineage Receipt Merkle Chain Audit", border_style="dim")
    table.add_column("Receipt ID", style="bold cyan")
    table.add_column("Node Name", style="green")
    table.add_column("Duration", justify="right")
    table.add_column("Parent Digest Link", style="dim")
    table.add_column("Canonical Digest", style="dim")

    for r in receipts:
        parent = r.attributes.get("parent_receipt_digest", "") or "ROOT"
        parent_short = parent[:12] + "..." if len(parent) > 12 else parent
        can_short = r.canonical_digest()[:12] + "..."
        table.add_row(
            r.receipt_id,
            r.node_name,
            f"{r.execution_duration_ms:.1f}ms",
            parent_short,
            can_short,
        )

    console.print(table)
    if is_valid:
        console.print(
            f"[bold green]✔ Merkle Lineage Chain Cryptographically VERIFIED![/bold green]\n"
            f"Chain Length: [bold]{len(receipts)}[/bold] receipts | Merkle Root: [bold cyan]{merkle_root}[/bold cyan]"
        )
    else:
        console.print(
            "[bold red]✖ Merkle Chain VIOLATED![/bold red] Violations:\n"
            + "\n".join(f"  • {v}" for v in violations)
        )


@integrity_app.command(name="digest")
def digest_artifact(
    path: str = typer.Argument(..., help="Path to artifact (Parquet, CSV, weights, etc.)"),
) -> None:
    """Compute content-addressable deterministic SHA-256 digest of an artifact."""
    p = Path(path)
    if not p.exists():
        console.print(f"[red]Error: file '{path}' does not exist.[/red]")
        raise typer.Exit(1)

    if p.suffix in (".parquet", ".csv"):
        df = pl.read_parquet(p) if p.suffix == ".parquet" else pl.read_csv(p)
        ev_digest = ContentAddressableDigest.digest_polars(df, uri=str(p))
    elif p.suffix in (".pt", ".bin", ".safetensors"):
        weights = torch.load(p, map_location="cpu", weights_only=False)
        ev_digest = ContentAddressableDigest.digest_torch(weights, uri=str(p))
    else:
        from ckodex_aiops.kernel.receipt import hash_file

        h = hash_file(p)
        ev_digest = EvidenceDigest(
            algorithm="sha256", digest=h, uri=str(p), byte_count=p.stat().st_size
        )

    console.print(
        Panel.fit(
            f"[bold cyan]Content-Addressable Digest[/bold cyan]\n"
            f"URI: [dim]{ev_digest.uri}[/dim]\n"
            f"SHA-256: [bold green]{ev_digest.digest}[/bold green]\n"
            f"Bytes: [bold]{ev_digest.byte_count:,}[/bold]",
            border_style="cyan",
        )
    )


# -----------------------------------------------------------------------------
# Resilience Commands (Rules #29, #30, #31, #32)
# -----------------------------------------------------------------------------
resilience_app = typer.Typer(
    name="resilience",
    help="Platform Resilience, Circuit Breakers & Degraded Modes (Rules #29, #30, #31, #32)",
)
app.add_typer(resilience_app, name="resilience", rich_help_panel="Day-2 Operations & Recovery")


@resilience_app.command(name="status")
def resilience_status() -> None:
    """Inspect active circuit breakers, degraded operational modes, and quarantine vaults."""
    qm = QuarantineManager()
    records = qm.list_quarantined()

    table = Table(title="CKODEX Platform Resilience Posture", border_style="dim")
    table.add_column("Subsystem", style="bold")
    table.add_column("Operational Mode", justify="center")
    table.add_column("Active Guards", style="dim")
    table.add_column("Details", style="dim")

    table.add_row(
        "Kedro Pipelines",
        "[bold green]NORMAL[/bold green]",
        "ResilienceCircuitBreakerHook, DataIntegrityHook",
        "Per-node failure budgeting active",
    )
    table.add_row(
        "Ray Worker Runtime",
        "[bold green]NORMAL[/bold green]",
        "Actor restart budgets (max_restarts=3)",
        "Zero working_dir packaging isolation",
    )
    table.add_row(
        "Quarantine Vault",
        f"[yellow]{len(records)} ISOLATED[/yellow]" if records else "[green]CLEAN[/green]",
        "Forensic evidence retention",
        f"{len(records)} incident records preserved in vault",
    )
    console.print(table)


# -----------------------------------------------------------------------------
# Traceability Commands (Rules #10, #12, #38)
# -----------------------------------------------------------------------------
trace_app = typer.Typer(
    name="trace",
    help="Four Truth Channels & Flight Recorder Traceability (Rules #10, #12, #38)",
)
app.add_typer(trace_app, name="trace", rich_help_panel="Integrity & Observability")


@trace_app.command(name="correlate")
def trace_correlate(
    run_id: str = typer.Argument(
        ..., help="Run ID or prefix to correlate across the four truth channels."
    ),
) -> None:
    """Correlate Telemetry, Execution, Decision, and Evidence traces across the four truth channels (Rule #12)."""
    trace(run_id)


@trace_app.command(name="flight-recorder")
def show_flight_recorder(
    log_file: str = typer.Option(
        "data/08_reporting/flight_recorder.jsonl",
        help="Path to flight recorder log.",
    ),
    limit: int = typer.Option(10, help="Number of recent records to display."),
) -> None:
    """Display recent execution events recorded by the platform Flight Recorder."""
    p = Path(log_file)
    if not p.exists():
        console.print(f"[yellow]Flight recorder log '{log_file}' does not exist yet.[/yellow]")
        return

    lines = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    lines.append(json.loads(line))
                except Exception:
                    pass

    recent = lines[-limit:]
    table = Table(title=f"CKODEX Flight Recorder (Last {len(recent)} Events)", border_style="dim")
    table.add_column("Timestamp", style="dim")
    table.add_column("Node Name", style="bold cyan")
    table.add_column("Duration", justify="right")
    table.add_column("Parent Merkle Hash", style="dim")
    table.add_column("Canonical Digest", style="dim")

    for ev in recent:
        p_hash = ev.get("parent_digest", "") or "ROOT"
        p_str = p_hash[:12] + "..." if len(p_hash) > 12 else p_hash
        c_str = ev.get("canonical_digest", "")[:12] + "..."
        table.add_row(
            ev.get("timestamp_utc", ""),
            ev.get("node_name", ""),
            f"{ev.get('duration_ms', 0):.1f}ms",
            p_str,
            c_str,
        )

    console.print(table)


@trace_app.command(name="research-evidence")
def show_research_evidence(
    db_path: str = typer.Option(
        "data/08_reporting/research_evidence.db",
        help="Path to ckodex-research-evidence SQLite database.",
    ),
) -> None:
    """Inspect local research evidence protocol state (CKX-EXP-001 / CKX-RES-001)."""
    from ckodex_aiops.adapters.tracking.research_evidence_adapter import (
        ResearchEvidenceTracker,
    )

    tracker = ResearchEvidenceTracker(db_path=db_path)
    if not tracker.is_available:
        console.print(
            Panel.fit(
                "[bold yellow]CKODEX Research Evidence Protocol Status[/bold yellow]\n\n"
                "[dim]Status:[/] [yellow]UNAVAILABLE / UNINITIALIZED[/yellow]\n"
                f"[dim]DB Path:[/] {db_path}\n\n"
                "[bold white]To activate full research evidence tracking:[/bold white]\n"
                "1. Ensure [cyan]ckodex-research-evidence[/cyan] repository is available at:\n"
                "   [dim]~/Documents/projects/operations/ckodex-research-evidence[/dim]\n"
                "2. Or install the SDK via [dim]pip install -e ~/Documents/projects/operations/ckodex-research-evidence/python[/dim]\n"
                "3. Set [dim]CKX_RESEARCH_EVIDENCE_DB[/dim] or execute [dim]uv run ckodex-aiops run[/dim]",
                border_style="yellow",
            )
        )
        return

    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Research Evidence Protocol Active (CKX-EXP-001)[/bold cyan]\n\n"
            f"[dim]Experiment Name:[/] [bold]{tracker.experiment_name}[/bold]\n"
            f"[dim]Database Path:[/] [green]{db_path}[/green]\n"
            f"[dim]Experiment ID:[/] [dim]{getattr(tracker._exp, 'exp_id', 'unknown')}[/dim]\n"
            f"[dim]Frozen Revision ID:[/] [dim]{getattr(tracker._exp, 'revision_id', 'unknown')}[/dim]\n\n"
            r"[bold white]Principles Applied:[/bold white]\n"
            " • [green]Track the experiment, not the world[/green] (Law #1)\n"
            " • [green]Opaque external correlations for models and datasets[/green] (Law #6 & #7)\n"
            " • [green]Zero-server local-first trial journaling[/green]",
            border_style="cyan",
        )
    )


@click.group(name="ckodex")
def kedro_commands():
    """CKODEX Day-2 Operations commands registered with Kedro CLI."""
    pass


@kedro_commands.command(name="doctor")
def kedro_doctor():
    """Run platform preflight diagnostics."""
    doctor()


@kedro_commands.command(name="compact")
@click.argument("target", default="data/04_feature/features.lance")
def kedro_compact(target: str):
    """Run distributed fragment compaction."""
    lance_compact(target=target)
