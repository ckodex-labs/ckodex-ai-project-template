"""
Unit & Integration Tests for CKODEX-DS-3 Evidence Editorial Mission Cockpit & Tour.
Validates telemetry collection, HTML generation, and CLI commands.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ckodex_aiops.adapters.observability.cockpit import AiopsCockpit
from ckodex_aiops.cli import app
from ckodex_aiops.kernel.state_vector import Anti, StateVector

runner = CliRunner()


def test_cockpit_telemetry_collection():
    ui = AiopsCockpit()
    data = ui.collect_telemetry()

    assert "profile" in data
    assert "accelerator" in data
    assert "state_vector" in data
    assert "ray_info" in data
    assert "merkle_root" in data
    assert "datasets" in data
    vec = data["state_vector"]
    assert isinstance(vec, StateVector)
    assert vec.anti == Anti.NONE


def test_cockpit_html_export_ds3_compliance(tmp_path: Path):
    ui = AiopsCockpit()
    out_file = tmp_path / "test_cockpit.html"
    res = ui.export_html(output_path=out_file)

    assert res.exists()
    content = res.read_text(encoding="utf-8")

    # Verify CKODEX-DS-3 tokens & vocabulary
    assert "CKODEX-DS-3" in content
    assert 'data-theme="vault"' in content
    assert "--ck-paper" in content
    assert "--ck-rust" in content
    assert "--ck-violet" in content
    assert "Evidence Margin" in content
    assert "mode changes deployment, not governance semantics" in content
    assert "Instrument Serif" in content
    assert "JetBrains Mono" in content
    assert "State Vector Radar S(e,t)" in content
    assert "Interactive Merkle Lineage Pipeline DAG" in content


def test_cli_cockpit_export(tmp_path: Path):
    target = str(tmp_path / "cockpit_cli.html")
    result = runner.invoke(app, ["cockpit", "--export-html", target])
    assert result.exit_code == 0
    assert Path(target).exists()


def test_cli_tour_execution():
    result = runner.invoke(app, ["tour", "--no-browser"])
    assert result.exit_code == 0
    assert "ACT I: SUBSTRATE & PREFLIGHT DOCTOR" in result.output
    assert "ACT VII: AUTONOMIC DAY-2 RECONCILER" in result.output
    assert "High-Assurance Architectural Tour Complete" in result.output


def test_cockpit_server_api_endpoints():
    import json
    import threading
    import urllib.request

    ui = AiopsCockpit()
    server = ui.create_server(port=0)
    port = server.server_address[1]

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    base_url = f"http://127.0.0.1:{port}"
    try:
        # 1. Healthz
        with urllib.request.urlopen(f"{base_url}/healthz") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "HEALTHY"

        # 2. Telemetry API
        with urllib.request.urlopen(f"{base_url}/api/telemetry") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert "state_vector" in data
            assert "presence" in data["state_vector"]
            assert "merkle_root" in data

        # 3. HTML dynamic render
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == 200
            html = resp.read().decode()
            assert "CKODEX-DS-3" in html

        # 4. Reconcile POST API
        req = urllib.request.Request(f"{base_url}/api/reconcile", data=b"{}", method="POST")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["status"] == "RECONCILED"
            assert "receipt_id" in data
    finally:
        server.shutdown()
        server.server_close()
