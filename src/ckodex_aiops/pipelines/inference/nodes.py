"""
Distributed Inference Pipeline Nodes.
Serves high-throughput PyTorch model predictions using a stateful Ray Actor pool.
"""

from __future__ import annotations

from typing import Any

import polars as pl
from rich.console import Console

from ckodex_aiops.adapters.ray.actors.pool import ActorPoolManager
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager

console = Console()


def run_distributed_inference(
    model_artifact: dict[str, Any],
    features_df: pl.DataFrame,
    num_actors: int = 2,
    batch_size: int = 128,
) -> pl.DataFrame:
    """
    Executes distributed batch inference with stateful PyTorch InferenceActors.
    """
    RayRuntimeManager.initialize()

    metadata = model_artifact["metadata"]
    state_dict = model_artifact["state_dict"]

    vecs = features_df["vector"].to_list()
    total_samples = len(vecs)

    chunks = [vecs[i : i + batch_size] for i in range(0, total_samples, batch_size)]

    console.print(
        f"[cyan]Dispatching inference for {total_samples} samples across {num_actors} PyTorch Ray Actors...[/cyan]"
    )

    pool = ActorPoolManager.create_inference_pool(
        size=num_actors,
        model_state_dict=state_dict,
        input_dim=metadata["input_dim"],
        hidden_dim=metadata.get("hidden_dim", 64),
        num_classes=metadata["num_classes"],
    )

    try:
        results = pool.dispatch_batch("predict_batch", chunks)

        all_preds = []
        all_workers = []
        for res in results:
            preds = res["predictions"]
            worker = res["worker_id"]
            all_preds.extend(preds)
            all_workers.extend([worker] * len(preds))

        predictions_df = features_df.with_columns(
            [
                pl.Series("predicted_class", all_preds),
                pl.Series("inference_worker_id", all_workers),
            ]
        )

        console.print(
            f"[bold green]✔ Distributed Inference Complete:[/bold green] {predictions_df.height} records scored."
        )
        return predictions_df

    finally:
        pool.terminate()
