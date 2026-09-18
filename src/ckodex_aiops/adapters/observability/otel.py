"""
OpenTelemetry (OTEL) & W3C TraceContext Propagation (Rule #12).
Provides distributed tracing, span creation, and context propagation across
Kedro pipelines and stateful Ray Actors.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

from opentelemetry import context, trace
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Status, StatusCode


class OtelTracerManager:
    """
    OpenTelemetry manager with W3C TraceContext carrier injection and extraction.
    """

    _initialized: bool = False
    _tracer: trace.Tracer | None = None

    @classmethod
    def initialize(cls, service_name: str = "ckodex-aiops") -> trace.Tracer:
        if not cls._initialized:
            resource = Resource.create({"service.name": service_name, "framework": "ckodex-gal1"})
            provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(provider)
            cls._tracer = trace.get_tracer("ckodex.aiops.tracer")
            cls._initialized = True
        return cls._tracer  # type: ignore

    @classmethod
    def get_tracer(cls) -> trace.Tracer:
        if not cls._initialized:
            return cls.initialize()
        return cls._tracer  # type: ignore

    @classmethod
    def inject_context(cls, carrier: dict[str, str] | None = None) -> dict[str, str]:
        """
        Injects W3C traceparent into a dictionary carrier for propagation across Ray actors.
        """
        if carrier is None:
            carrier = {}
        inject(carrier)
        return carrier

    @classmethod
    def extract_context(cls, carrier: dict[str, str]) -> Any:
        """
        Extracts W3C traceparent from a dictionary carrier at the Ray worker / RPC boundary.
        """
        return extract(carrier)

    @classmethod
    @contextlib.contextmanager
    def trace_span(
        cls,
        name: str,
        carrier: dict[str, str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[trace.Span]:
        """
        Context manager to create and propagate spans across boundaries.
        """
        tracer = cls.get_tracer()
        token = None
        if carrier:
            extracted_ctx = cls.extract_context(carrier)
            token = context.attach(extracted_ctx)

        with tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, str(v))
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, description=str(e)))
                span.record_exception(e)
                raise
            finally:
                if token:
                    context.detach(token)
