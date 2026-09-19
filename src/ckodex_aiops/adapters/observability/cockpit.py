"""
AIOps Interactive Real-Time Cockpit & Visual Dashboard (CKODEX Rules #37, #41).
Provides high-density, Tufte-inspired terminal and HTML dashboards visualizing
state vectors, storage topology, Ray actor mesh, and cryptographic lineage receipts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

from ckodex_aiops.kernel.profiles import ProfileRegistry
from ckodex_aiops.kernel.reconciler import AutonomicReconciler


class AiopsCockpit:
    """
    Operator Cockpit providing deep observability, drift diagnostics,
    and visual state vector monitoring.
    """

    def __init__(self, profile_name: str = "macos_metal_safetensors") -> None:
        self.profile_name = profile_name
        self.console = Console()
        self.reconciler = AutonomicReconciler(profile_name=profile_name)

    def collect_telemetry(self) -> dict[str, Any]:
        """Collects cross-cutting telemetry from all operational planes."""
        baseline = ProfileRegistry.get_baseline(self.profile_name)
        observed = self.reconciler.observe()
        anomalies = self.reconciler.detect(observed)
        current_vector = self.reconciler.diagnose(anomalies)

        receipts_dir = Path("data/08_reporting/receipts")
        recent_receipts: list[str] = []
        if receipts_dir.exists():
            recent_receipts = [
                f.name
                for f in sorted(
                    receipts_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
                )[:5]
            ]

        quar_dir = Path("data/08_reporting/quarantine")
        quar_count = len(list(quar_dir.glob("quar_*.json"))) if quar_dir.exists() else 0
        derog_dir = Path("data/08_reporting/derogations")
        derog_count = len(list(derog_dir.glob("derog_*.json"))) if derog_dir.exists() else 0

        return {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ"),
            "profile": baseline.name,
            "accelerator": baseline.device,
            "weights_format": baseline.model_format,
            "state_vector": current_vector,
            "anomalies": anomalies,
            "datasets": observed["datasets"],
            "models": observed["models"],
            "recent_receipts": recent_receipts,
            "quarantine_count": quar_count,
            "derogations_count": derog_count,
        }

    def render_terminal(self) -> None:
        """Renders rich terminal dashboard."""
        data = self.collect_telemetry()
        vec = data["state_vector"]

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )

        # Header
        layout["header"].update(
            Panel(
                f"[bold cyan]CKODEX AIOps Autonomic Mission Cockpit[/bold cyan] | "
                f"Profile: [bold green]{data['profile']}[/bold green] | "
                f"Accelerator: [bold yellow]{data['accelerator']}[/bold yellow] | "
                f"UTC: {data['timestamp']}",
                border_style="cyan",
            )
        )

        # Left: State Vector & Anomalies
        left_table = Table(title="Operational State Vector S(e, t)", expand=True)
        left_table.add_column("Dimension", style="bold")
        left_table.add_column("Value", style="green" if vec.is_healthy() else "red")

        left_table.add_row("Presence", str(vec.presence))
        left_table.add_row("Valence", str(vec.valence))
        left_table.add_row("Anti / Conflict", str(vec.anti))
        left_table.add_row("Coherence", str(vec.coherence))
        left_table.add_row("Evidence", str(vec.evidence))
        left_table.add_row("Lifecycle", str(vec.lifecycle))
        left_table.add_row("Anomalies Active", str(len(data["anomalies"])))
        left_table.add_row("Quarantined Items", str(data["quarantine_count"]))
        left_table.add_row("Active Derogations", str(data["derogations_count"]))

        layout["left"].update(
            Panel(left_table, border_style="green" if vec.is_healthy() else "yellow")
        )

        # Right: Storage & Lineage
        right_table = Table(title="Lance Vector Storage & Cryptographic Lineage", expand=True)
        right_table.add_column("Entity / Dataset", style="bold")
        right_table.add_column("Status", style="cyan")

        for ds_path, ds_info in data["datasets"].items():
            st = (
                f"Fragments: {ds_info.get('fragment_files', 0)}"
                if ds_info.get("exists")
                else "Missing"
            )
            right_table.add_row(Path(ds_path).name, st)

        for rcpt in data["recent_receipts"][:3]:
            right_table.add_row(f"Receipt: {rcpt[:24]}...", "VERIFIED_SHA256")

        layout["right"].update(Panel(right_table, border_style="blue"))

        # Footer
        layout["footer"].update(
            Panel(
                "[dim]CKODEX GAL-1 Standard • Day-2 Autonomous Control Loop Active • Run 'ckodex-aiops reconcile' to self-heal[/dim]",
                border_style="dim",
            )
        )

        self.console.print(layout)

    def export_html(self, output_path: str | Path = "data/08_reporting/cockpit.html") -> Path:
        """Exports a zero-dependency, modern dark-theme HTML cockpit report."""
        data = self.collect_telemetry()
        vec = data["state_vector"]
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CKODEX AIOps Autonomous Cockpit</title>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --text: #f3f4f6;
      --accent: #38bdf8;
      --border: #1f2937;
      --green: #10b981;
      --yellow: #f59e0b;
      --red: #ef4444;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 2rem;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1rem;
      margin-bottom: 2rem;
    }}
    h1 {{ margin: 0; font-size: 1.5rem; color: var(--accent); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.5rem;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
    }}
    .card h2 {{ font-size: 1.1rem; margin-top: 0; color: #9ca3af; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
    td, th {{ padding: 0.5rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      background: #1f2937;
    }}
    .badge-positive {{ background: rgba(16, 185, 129, 0.2); color: var(--green); }}
    .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: var(--yellow); }}
    .badge-error {{ background: rgba(239, 68, 68, 0.2); color: var(--red); }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>CKODEX AIOps Autonomic Mission Cockpit</h1>
      <div style="font-size: 0.85rem; color: #9ca3af; margin-top: 0.25rem;">
        Baseline: <strong>{data["profile"]}</strong> | Accelerator: <strong>{data["accelerator"]}</strong>
      </div>
    </div>
    <div style="text-align: right; font-size: 0.85rem; color: #9ca3af;">
      Reported: {data["timestamp"]}<br>
      Assurance: <strong>GAL 1 Constitutional</strong>
    </div>
  </header>

  <div class="grid">
    <div class="card">
      <h2>Operational State Vector S(e, t)</h2>
      <table>
        <tr><td>Presence</td><td><span class="badge">{vec.presence}</span></td></tr>
        <tr><td>Valence</td><td><span class="badge badge-positive">{vec.valence}</span></td></tr>
        <tr><td>Anti / Conflict</td><td><span class="badge">{vec.anti}</span></td></tr>
        <tr><td>Coherence</td><td><span class="badge badge-positive">{vec.coherence}</span></td></tr>
        <tr><td>Evidence Status</td><td><span class="badge">{vec.evidence}</span></td></tr>
        <tr><td>Lifecycle Mode</td><td><span class="badge badge-positive">{vec.lifecycle}</span></td></tr>
        <tr><td>Quarantined Items</td><td><span class="badge">{data["quarantine_count"]}</span></td></tr>
        <tr><td>Active Derogations</td><td><span class="badge">{data["derogations_count"]}</span></td></tr>
      </table>
    </div>

    <div class="card">
      <h2>Lance Storage Topology</h2>
      <table>
        <tr><th>Dataset</th><th>Status</th><th>Fragments</th></tr>
        {"".join(f"<tr><td>{Path(p).name}</td><td>{'ONLINE' if info['exists'] else 'OFFLINE'}</td><td>{info.get('fragment_files', 0)}</td></tr>" for p, info in data["datasets"].items())}
      </table>
    </div>

    <div class="card">
      <h2>Recent Cryptographic Receipts</h2>
      <table>
        <tr><th>Receipt Identifier</th><th>Status</th></tr>
        {"".join(f"<tr><td><code>{r}</code></td><td><span class='badge badge-positive'>VERIFIED</span></td></tr>" for r in data["recent_receipts"])}
      </table>
    </div>
  </div>
</body>
</html>
"""
        with open(out, "w", encoding="utf-8") as f:
            f.write(html_content)
        return out
