"""
Tests for Physical AI Multimodal Telemetry and Data Mining.
"""

from __future__ import annotations

from pathlib import Path

import torch

from ckodex_aiops.models.streaming_dataset import StreamingLanceTorchDataset
from ckodex_aiops.pipelines.physical_ai.nodes import (
    extract_kinematic_features_and_events,
    generate_multimodal_robotics_telemetry,
    ingest_physical_ai_dataset,
    mine_physical_ai_events,
)


def test_generate_and_extract_physical_ai(tmp_path: Path):
    # 1. Generate multi-modal robotics telemetry
    df = generate_multimodal_robotics_telemetry(
        num_episodes=2, steps_per_episode=20, embedding_dim=16
    )
    assert len(df) == 40
    assert "accel_x" in df.columns
    assert "raw_sensor_embedding" in df.columns
    assert len(df["raw_sensor_embedding"][0]) == 16

    # 2. Extract rolling kinematic features and event flags
    processed = extract_kinematic_features_and_events(df, window_size=3)
    assert "accel_mag" in processed.columns
    assert "jerk_mag" in processed.columns
    assert "slip_detected" in processed.columns
    assert "anomaly_flag" in processed.columns
    assert processed["accel_mag"].null_count() == 0

    # 3. Ingest into Lance storage
    lance_path = str(tmp_path / "physical_ai_test.lance")
    written_path = ingest_physical_ai_dataset(processed, target_path=lance_path)
    assert written_path == lance_path

    # 4. Mine physical AI events with pushdown SQL filter
    report = mine_physical_ai_events(lance_path, filter_expr="accel_mag > 0.0", limit=5)
    assert report["total_matched_samples"] <= 5
    assert len(report["sample_events"]) > 0


def test_streaming_lance_torch_dataset_physical_ai(tmp_path: Path):
    # Generate and ingest small dataset
    df = generate_multimodal_robotics_telemetry(
        num_episodes=2, steps_per_episode=30, embedding_dim=8
    )
    processed = extract_kinematic_features_and_events(df, window_size=3)
    lance_path = str(tmp_path / "streaming_physical_ai.lance")
    ingest_physical_ai_dataset(processed, target_path=lance_path)

    # Instantiate streaming dataset with pushdown filter
    streaming_ds = StreamingLanceTorchDataset(
        uri=lance_path,
        filter_expr="step_id < 15",
        batch_size=10,
        feature_col="raw_sensor_embedding",
        label_col=None,
    )

    loader = streaming_ds.create_dataloader()
    batches = list(loader)
    assert len(batches) > 0

    first_feat, first_label = batches[0]
    assert isinstance(first_feat, torch.Tensor)
    assert first_feat.shape[1] == 8
    assert first_label is None
