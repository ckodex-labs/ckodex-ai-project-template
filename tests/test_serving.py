"""Tests for Model Serving Gateway and HTTP Transport.
Validates health endpoints, liveness, dynamic batch inference, and execution receipts.
"""

from __future__ import annotations

import json
import threading
import urllib.request

from ckodex_aiops.adapters.serving.gateway import ModelServingGateway


def test_model_serving_gateway_lifecycle():
    """Serving gateway must respond to /healthz, /livez, and /v1/models/classifier/infer."""
    # Find ephemeral port
    port = 18991
    gateway = ModelServingGateway(
        model_weights_path="data/06_models/model.safetensors",
        input_dim=16,
        num_classes=3,
        device="cpu",
        port=port,
    )
    server = gateway.create_server(host="127.0.0.1")

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Healthz
        with urllib.request.urlopen(f"{base_url}/healthz") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "HEALTHY"

        # 2. Livez
        with urllib.request.urlopen(f"{base_url}/livez") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ALIVE"

        # 3. Infer POST
        payload = json.dumps({"inputs": [[0.5] * 32, [0.1] * 32]}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/v1/models/classifier/infer",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
            },
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "predictions" in data
            assert len(data["predictions"]) == 2
            assert "probabilities" in data
            assert len(data["probabilities"]) == 2
            assert "receipt_digest" in data
            assert len(data["receipt_digest"]) == 64
    finally:
        server.shutdown()
        server.server_close()
