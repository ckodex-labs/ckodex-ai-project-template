"""
Kedro Hook: Traceability, W3C Trace Context & Four Truth Channels Evidence (Rules #10, #12, #18, #37, #38).
Implements:
1. W3C Trace Context generation & propagation (traceparent / tracestate).
2. Four Truth Channels correlation: Telemetry + Execution + Decision + Evidence.
3. Cryptographic Merkle Lineage Chaining (parent_receipt_digest links).
4. Immutable Flight Recorder logging for Day-2 diagnosis, audit, and governed replay.
"""

from __future__ import annotations

import json
import os
import resource
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from kedro.framework.hooks import hook_impl
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from rich.console import Console

from ckodex_aiops.kernel.integrity import ContentAddressableDigest
from ckodex_aiops.kernel.receipt import EvidenceDigest, LineageReceipt

console = Console()


class TraceabilityEvidenceHook:
    """
    Captures complete 4-channel telemetry, W3C trace propagation, and cryptographic receipts.
    """

    def __init__(
        self,
        output_dir: str = "data/08_reporting/receipts",
        flight_recorder_file: str = "data/08_reporting/flight_recorder.jsonl",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.flight_recorder_path = Path(flight_recorder_file)
        self.flight_recorder_path.parent.mkdir(parents=True, exist_ok=True)

        self._trace_id: str = ""
        self._last_receipt_digest: str = ""
        self._node_metrics: dict[str, dict[str, Any]] = {}

    def _generate_w3c_traceparent(self) -> str:
        """Generates valid W3C traceparent header: 00-{trace_id_32hex}-{span_id_16hex}-01."""
        trace_id = self._trace_id or uuid4().hex
        span_id = uuid4().hex[:16]
        return f"00-{trace_id}-{span_id}-01"

    @hook_impl
    def before_pipeline_run(
        self,
        run_params: dict[str, Any],
        pipeline: Pipeline,
        catalog: Any,
    ) -> None:
        self._trace_id = uuid4().hex
        self._last_receipt_digest = ""
        os.environ["TRACEPARENT"] = self._generate_w3c_traceparent()
        console.print(
            f"[bold cyan]⠹ Traceability Hook:[/bold cyan] Active W3C Trace ID: [dim]{self._trace_id}[/dim]"
        )

    @hook_impl
    def before_node_run(
        self,
        node: Node,
        catalog: Any,
        inputs: dict[str, Any],
        is_async: bool,
    ) -> None:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        self._node_metrics[node.name] = {
            "start_time": time.perf_counter(),
            "cpu_user_start": usage.ru_utime,
            "cpu_system_start": usage.ru_stime,
            "max_rss_start_kb": usage.ru_maxrss,
            "traceparent": self._generate_w3c_traceparent(),
        }

    @hook_impl
    def after_node_run(
        self,
        node: Node,
        catalog: Any,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        is_async: bool,
    ) -> None:
        metrics = self._node_metrics.pop(node.name, {})
        start_time = metrics.get("start_time", time.perf_counter())
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        usage = resource.getrusage(resource.RUSAGE_SELF)
        cpu_user_delta = usage.ru_utime - metrics.get("cpu_user_start", usage.ru_utime)
        cpu_sys_delta = usage.ru_stime - metrics.get("cpu_system_start", usage.ru_stime)
        max_rss_kb = usage.ru_maxrss

        receipt_id = f"rcpt_{uuid4().hex[:12]}"
        intent_id = f"intent_{node.name}_{int(time.time())}"

        # 1. Digest inputs and outputs deterministically
        input_digests: list[EvidenceDigest] = []
        for in_name, in_val in inputs.items():
            input_digests.append(
                ContentAddressableDigest.digest(in_val, uri=f"catalog://{in_name}")
            )

        output_digests: list[EvidenceDigest] = []
        for out_name, out_val in outputs.items():
            output_digests.append(
                ContentAddressableDigest.digest(out_val, uri=f"catalog://{out_name}")
            )

        # 2. Construct Merkle-linked LineageReceipt
        receipt = LineageReceipt(
            receipt_id=receipt_id,
            intent_id=intent_id,
            node_name=node.name,
            authority_urn="urn:ckodex:cfyd:aiops:prod:pipeline",
            input_digests=tuple(input_digests),
            output_digests=tuple(output_digests),
            execution_duration_ms=round(duration_ms, 2),
            attributes={
                "parent_receipt_digest": self._last_receipt_digest,
                "w3c_traceparent": metrics.get("traceparent", ""),
                "trace_id": self._trace_id,
                "inputs_count": len(inputs),
                "outputs_count": len(outputs),
                "async_execution": is_async,
                "telemetry": {
                    "duration_ms": round(duration_ms, 2),
                    "cpu_user_sec": round(cpu_user_delta, 4),
                    "cpu_system_sec": round(cpu_sys_delta, 4),
                    "max_rss_kb": max_rss_kb,
                },
            },
        )

        canonical_digest = receipt.canonical_digest()
        self._last_receipt_digest = canonical_digest

        # 3. Write individual receipt JSON
        receipt_path = self.output_dir / f"{receipt_id}_{node.name}.json"
        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(receipt.to_dict(), f, indent=2)

        # 4. Append to Flight Recorder log (Rule #38)
        flight_record = {
            "timestamp_utc": receipt.timestamp_utc,
            "trace_id": self._trace_id,
            "receipt_id": receipt_id,
            "node_name": node.name,
            "canonical_digest": canonical_digest,
            "parent_digest": receipt.attributes.get("parent_receipt_digest", ""),
            "duration_ms": duration_ms,
            "inputs_digests": [d.digest for d in input_digests],
            "output_digests": [d.digest for d in output_digests],
        }
        with open(self.flight_recorder_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(flight_record) + "\n")

        console.print(
            f"[dim green]  └─ Merkle Receipt Emitted:[/dim green] [dim]{receipt_id} "
            f"({duration_ms:.1f}ms | Merkle parent: {receipt.attributes.get('parent_receipt_digest', 'ROOT')[:8]}...)[/dim]"
        )
