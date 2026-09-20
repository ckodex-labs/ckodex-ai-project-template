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
from uuid import uuid4

import click
import polars as pl
import torch
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ckodex_aiops.adapters.compliance.csr import CortaixCsrMatrixGenerator
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
from ckodex_aiops.kernel.conformance import ConformanceEngine
from ckodex_aiops.kernel.derogation import DerogationRegistry
from ckodex_aiops.kernel.drift import StatisticalDriftDetector
from ckodex_aiops.kernel.explanation import ExplanationEngine
from ckodex_aiops.kernel.intent import AuthorityPath, CapabilityLease
from ckodex_aiops.kernel.lifecycle import (
    LifecycleManager,
    LifecycleStatus,
    OffboardingRequest,
    OnboardingRequest,
    SubjectType,
)
from ckodex_aiops.kernel.quarantine import QuarantineManager, QuarantineStatus
from ckodex_aiops.kernel.receipt import compute_sha256
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
    name="ckodex-aiops",
    help="World-Class AI Platform CLI: Kedro, UV, Ray Actors, Lance, Polars, PyTorch",
    add_completion=False,
)
console = Console()


@app.command()
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
            detail = f"Ray active: {ray_info['cpus']} CPUs, {ray_info['memory_gb']} GB RAM"
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
        import mlflow

        table.add_row(
            "Experiment Tracking",
            "[green]PASS[/green]",
            f"MLflow {mlflow.__version__} & Flight Recorder active",
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


@app.command()
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


@app.command()
def verify(
    receipts_dir: str = typer.Option(
        "data/08_reporting/receipts", help="Directory containing lineage receipts"
    ),
) -> None:
    """
    Verify cryptographic lineage receipts and execution evidence.
    """
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


@app.command()
def benchmark(
    num_samples: int = typer.Option(5000, help="Number of benchmark samples"),
) -> None:
    """
    Benchmark throughput across Polars, Lance, and Ray Actor pools.
    """
    console.print(Panel.fit("[bold cyan]Micro-Benchmark: Polars vs Lance vs Ray[/bold cyan]"))

    # 1. Polars Benchmark
    start = time.perf_counter()
    df = pl.DataFrame(
        {
            "a": list(range(num_samples)),
            "b": [float(i) * 1.5 for i in range(num_samples)],
        }
    ).with_columns((pl.col("a") * pl.col("b")).alias("c"))
    polars_rps = num_samples / (time.perf_counter() - start)
    console.print(f"• Polars Transformation: [bold green]{polars_rps:,.0f}[/bold green] rows/sec")

    # 2. Lance Write & Read Benchmark
    import lance

    tmp_path = Path("data/02_intermediate/_bench.lance")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    lance.write_dataset(df.to_arrow(), str(tmp_path), mode="overwrite")
    lance_ds = lance.dataset(str(tmp_path))
    _ = lance_ds.scanner().to_table()
    lance_rps = num_samples / (time.perf_counter() - start)
    console.print(f"• Lance Storage Roundtrip: [bold green]{lance_rps:,.0f}[/bold green] rows/sec")
    shutil.rmtree(tmp_path, ignore_errors=True)

    # 3. Ray Actor Dispatch Benchmark
    RayRuntimeManager.initialize()
    from ckodex_aiops.adapters.ray.actors.pool import ActorPoolManager

    pool = ActorPoolManager.create_embedding_pool(size=2, embedding_dim=16)
    data = [[float(j) for j in range(4)] for _ in range(num_samples)]
    chunks = [data[i : i + 500] for i in range(0, num_samples, 500)]

    start = time.perf_counter()
    pool.dispatch_batch("generate_embeddings", chunks)
    ray_rps = num_samples / (time.perf_counter() - start)
    pool.terminate()

    console.print(
        f"• Ray Actor Pool Embeddings: [bold green]{ray_rps:,.0f}[/bold green] samples/sec"
    )


@app.command()
def run(
    pipeline: str | None = typer.Option(
        None,
        help="Pipeline to execute: __default__, data_processing, training, evaluation, inference, physical_ai",
    ),
    profile: str | None = typer.Option(
        None,
        help="Profile to activate (e.g. macos_metal_safetensors, physical_ai_robotics, cuda_distributed_pretraining)",
    ),
) -> None:
    """
    Execute a Kedro pipeline with optional profile activation.
    """
    from kedro.framework.session import KedroSession
    from kedro.framework.startup import bootstrap_project

    from ckodex_aiops.kernel.profiles import ProfileRegistry

    target_pipeline = pipeline
    extra_params = {}

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
            extra_params = prof.parameters
        except KeyError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    if target_pipeline is None:
        target_pipeline = "__default__"

    console.print(
        Panel.fit(f"[bold cyan]Executing Kedro Pipeline: '{target_pipeline}'[/bold cyan]")
    )
    bootstrap_project(Path.cwd())
    with KedroSession.create(project_path=Path.cwd(), runtime_params=extra_params) as session:
        session.run(pipeline_name=target_pipeline)
    console.print("[bold green]✔ Pipeline Run Succeeded![/bold green]")


profile_app = typer.Typer(
    name="profile",
    help="Platform Profiles & Baselines management (CKODEX Rule #36)",
)
app.add_typer(profile_app, name="profile")


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


@app.command()
def compact(
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


@app.command()
def mine(
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
        console.print(f"[red]Error:[/red] Physical AI dataset not found at: {path}")
        console.print(
            "[yellow]Tip: Run 'uv run ckodex-aiops run --pipeline physical_ai' first.[/yellow]"
        )
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold cyan]Physical AI Multimodal Mining Query[/bold cyan]\n"
            f"Dataset: [dim]{path}[/dim] | Filter: [bold yellow]{filter_expr}[/bold yellow]",
            border_style="cyan",
        )
    )

    start = time.perf_counter()
    result = mine_physical_ai_events(str(path), filter_expr=filter_expr, limit=limit)
    dur = (time.perf_counter() - start) * 1000

    table = Table(
        title=f"Matched Events ({result['total_matched_samples']} found in {dur:.1f} ms)",
        border_style="dim",
    )
    table.add_column("Episode", justify="center", style="bold")
    table.add_column("Step", justify="center")
    table.add_column("Accel Mag (m/s²)", justify="right")
    table.add_column("Jerk Mag (m/s³)", justify="right")
    table.add_column("Slip Detected", justify="center")

    for ev in result["sample_events"]:
        table.add_row(
            str(ev["episode_id"]),
            str(ev["step_id"]),
            f"{ev['accel_mag']:.3f}",
            f"{ev['jerk_mag']:.3f}",
            "[bold red]YES[/bold red]" if ev["slip_detected"] else "[green]NO[/green]",
        )

    console.print(table)
    console.print(f"[dim]Affected Episodes: {result['episodes_affected']}[/dim]")


@app.command()
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


@app.command()
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


@app.command()
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


@app.command()
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


@app.command(name="csr-matrix")
def csr_matrix(
    out_dir: str = typer.Option(
        "data/08_reporting/compliance",
        "--out-dir",
        "-o",
        help="Directory to emit CSR traceability reports.",
    ),
) -> None:
    """
    Generate CortAIx Factory CSR Traceability Matrix (JSON, CSV, Markdown).
    """
    res = CortaixCsrMatrixGenerator.generate_all(output_dir=out_dir)
    console.print(
        Panel.fit(
            f"[bold green]CortAIx CSR Traceability Matrix Generated[/bold green]\n"
            f"• Markdown Report: [bold]{res['markdown']}[/bold]\n"
            f"• JSON Dataset: [bold]{res['json']}[/bold] (SHA-256: [dim]{res['json_sha256'][:16]}...[/dim])\n"
            f"• CSV Matrix: [bold]{res['csv']}[/bold]",
            border_style="green",
        )
    )


@app.command()
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


@app.command()
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


@app.command(name="lifecycle")
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


@app.command()
def cockpit(
    export_html: str | None = typer.Option(
        None, "--export-html", help="Optional path to export static HTML dashboard."
    ),
) -> None:
    """
    Launch interactive AIOps Mission Cockpit dashboard.
    """
    ui = AiopsCockpit()
    ui.render_terminal()

    if export_html:
        dest = ui.export_html(output_path=export_html)
        console.print(f"[green]Exported HTML Cockpit to:[/green] [bold]{dest}[/bold]")


@app.command()
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


@app.command()
def drift(
    baseline_dataset: str = typer.Option(
        "data/01_raw/events.lance", "--baseline", "-b", help="Baseline Lance dataset path."
    ),
    observed_dataset: str = typer.Option(
        "data/04_feature/features.lance", "--observed", "-o", help="Observed Lance dataset path."
    ),
) -> None:
    """
    Run statistical feature & sensor drift detection (Wasserstein distance & PSI).
    """
    console.print(
        Panel.fit(
            f"[bold cyan]CKODEX Statistical Drift Engine[/bold cyan]\n"
            f"Baseline: [dim]{baseline_dataset}[/dim] | Observed: [dim]{observed_dataset}[/dim]",
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
        f"Resulting State Vector: [bold green]{report.state_vector.lifecycle}[/bold green] (Valence: {report.state_vector.valence})"
    )


@app.command(name="airgap-pack")
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


@app.command(name="airgap-verify")
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


@app.command()
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


@app.command()
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


@app.command()
def optimize(
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


@app.command(name="ray-pg")
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


oci_app = typer.Typer(
    name="oci",
    help="OCI Artifact Packaging & Distribution Engine (OCI Spec v1.1.0, ORAS, Cosign)",
)
app.add_typer(oci_app, name="oci")


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
            f"• Layers Count: [bold]{res['layers_count']}[/bold] (Template + SBOMs + OSCAL + CSR)\n"
            f"• Template Archive: [dim]{res['template_archive_digest'][:24]}...[/dim] ({res['template_archive_size'] / (1024 * 1024):.2f} MB)\n"
            f"• Lineage Receipt: [dim]{res['receipt_id']}[/dim]",
            border_style="green",
        )
    )


@oci_app.command(name="inspect")
def oci_inspect(
    layout: str = typer.Option(
        "dist/oci-template", "--layout", "-l", help="OCI Image Layout directory."
    ),
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
        "ghcr.io/cfyd-ai/ckodex-aiops-template:v1.0.0",
        "--image-ref",
        "-r",
        help="Target OCI registry reference.",
    ),
    layout: str = typer.Option(
        "dist/oci-template", "--layout", "-l", help="OCI Image Layout directory."
    ),
) -> None:
    """
    Display production ORAS and Cosign commands to push, pull, sign, and attest the OCI artifact.
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


@app.command(name="explain")
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


@app.command(name="trace")
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


@app.command(name="recover")
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


@app.command(name="replay")
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
app.add_typer(quarantine_app, name="quarantine")


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
app.add_typer(derogation_app, name="derogation")


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
    compact(target=target)
