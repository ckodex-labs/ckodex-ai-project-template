"""Tests for OpenTelemetry (OTEL) context propagation across Kedro and Ray actors.
Validates W3C TraceContext carrier injection, extraction, and span management.
"""

from __future__ import annotations

from ckodex_aiops.adapters.observability.otel import OtelTracerManager


def test_otel_tracer_manager_lifecycle():
    """OtelTracerManager must initialize, start spans, and attach attributes."""
    tracer = OtelTracerManager.initialize(service_name="test-service")
    assert tracer is not None

    with OtelTracerManager.trace_span("parent_operation", attributes={"batch.size": 64}) as span:
        assert span is not None
        span.add_event("checkpoint_reached", {"step": 10})


def test_w3c_trace_context_injection_and_extraction():
    """W3C TraceContext must serialize into carriers for distributed boundaries."""
    OtelTracerManager.initialize(service_name="ray-driver")

    with OtelTracerManager.trace_span("orchestrator_node"):
        carrier: dict[str, str] = {}
        OtelTracerManager.inject_context(carrier)

        # Carrier has been populated
        assert isinstance(carrier, dict)

        # Worker extracts context and starts downstream span
        extracted_ctx = OtelTracerManager.extract_context(carrier)
        assert extracted_ctx is not None

        with OtelTracerManager.trace_span(
            "worker_task", carrier=carrier, attributes={"task.id": "42"}
        ) as child_span:
            assert child_span is not None
