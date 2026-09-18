"""
Physical AI & Multimodal Telemetry Pipeline Nodes.
Processes high-frequency robotics/autonomous system sensor telemetry,
extracts rolling kinematic features via Polars, and leverages Lance single-table evolution
and hybrid vector/SQL search for fast physical event mining.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import lance
import numpy as np
import polars as pl
import pyarrow as pa


def generate_multimodal_robotics_telemetry(
    num_episodes: int = 10,
    steps_per_episode: int = 100,
    embedding_dim: int = 32,
) -> pl.DataFrame:
    """
    Simulates high-frequency (100 Hz) multi-modal robotics telemetry across multiple episodes.
    Includes IMU linear acceleration, gyroscope angular velocities, joint kinematics,
    gripper state, and simulated multi-modal vision/sensor embeddings.
    """
    total_steps = num_episodes * steps_per_episode
    rng = np.random.default_rng(seed=42)

    episode_ids = []
    step_ids = []
    timestamps_ns = []

    base_time_ns = 1_700_000_000_000_000_000
    step_duration_ns = 10_000_000  # 10ms = 100 Hz

    current_time = base_time_ns
    for ep in range(num_episodes):
        for st in range(steps_per_episode):
            episode_ids.append(ep)
            step_ids.append(st)
            timestamps_ns.append(current_time)
            current_time += step_duration_ns

    # Kinematic signals with occasional simulated slips/shocks
    t = np.linspace(0, num_episodes * 10, total_steps)
    accel_x = np.sin(t) + rng.normal(0, 0.1, total_steps)
    accel_y = np.cos(t) + rng.normal(0, 0.1, total_steps)
    accel_z = 9.81 + rng.normal(0, 0.05, total_steps)

    gyro_x = rng.normal(0, 0.05, total_steps)
    gyro_y = rng.normal(0, 0.05, total_steps)
    gyro_z = rng.normal(0, 0.05, total_steps)

    joint_pos_1 = np.sin(t * 0.5)
    joint_pos_2 = np.cos(t * 0.5)
    joint_vel_1 = 0.5 * np.cos(t * 0.5)
    joint_vel_2 = -0.5 * np.sin(t * 0.5)
    gripper_effort = np.clip(np.sin(t * 0.2) * 50.0 + 20.0, 0.0, 100.0)

    # Inject discrete physical events (e.g. slip, collision, high-jerk events)
    slip_indices = rng.choice(total_steps, size=max(1, total_steps // 25), replace=False)
    accel_x[slip_indices] += rng.uniform(2.5, 5.0, size=len(slip_indices))
    gyro_z[slip_indices] += rng.uniform(1.8, 3.5, size=len(slip_indices))

    # Generate multi-modal observation embeddings
    embeddings = rng.normal(0, 1.0, (total_steps, embedding_dim)).astype(np.float32)
    # Normalize embeddings to unit norm for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = (embeddings / norms).tolist()

    df = pl.DataFrame(
        {
            "episode_id": episode_ids,
            "step_id": step_ids,
            "timestamp_ns": timestamps_ns,
            "accel_x": accel_x.tolist(),
            "accel_y": accel_y.tolist(),
            "accel_z": accel_z.tolist(),
            "gyro_x": gyro_x.tolist(),
            "gyro_y": gyro_y.tolist(),
            "gyro_z": gyro_z.tolist(),
            "joint_pos_1": joint_pos_1.tolist(),
            "joint_pos_2": joint_pos_2.tolist(),
            "joint_vel_1": joint_vel_1.tolist(),
            "joint_vel_2": joint_vel_2.tolist(),
            "gripper_effort": gripper_effort.tolist(),
            "raw_sensor_embedding": embeddings,
        }
    )
    return df


def extract_kinematic_features_and_events(
    telemetry_df: pl.DataFrame,
    window_size: int = 5,
) -> pl.DataFrame:
    """
    Extracts rolling window kinematic features using high-performance Polars expressions.
    Identifies jerk spikes, angular velocity variance, and marks slip events.
    """
    # Polars windowed expressions per episode
    processed_df = (
        telemetry_df.sort(["episode_id", "step_id"])
        .with_columns(
            # Acceleration magnitude (excluding gravity baseline)
            accel_mag=(
                pl.col("accel_x").pow(2)
                + pl.col("accel_y").pow(2)
                + (pl.col("accel_z") - 9.81).pow(2)
            ).sqrt(),
            # Gyro magnitude
            gyro_mag=(
                pl.col("gyro_x").pow(2) + pl.col("gyro_y").pow(2) + pl.col("gyro_z").pow(2)
            ).sqrt(),
            # Kinematic Jerk (finite differences of acceleration)
            jerk_x=pl.col("accel_x").diff().over("episode_id").fill_null(0.0),
            jerk_y=pl.col("accel_y").diff().over("episode_id").fill_null(0.0),
            jerk_z=pl.col("accel_z").diff().over("episode_id").fill_null(0.0),
        )
        .with_columns(
            jerk_mag=(
                pl.col("jerk_x").pow(2) + pl.col("jerk_y").pow(2) + pl.col("jerk_z").pow(2)
            ).sqrt(),
            # Rolling std of acceleration over window
            rolling_accel_std=pl.col("accel_mag")
            .rolling_std(window_size=window_size)
            .over("episode_id")
            .fill_null(0.0),
        )
        .with_columns(
            # Discrete Physical Event Classification
            slip_detected=(pl.col("accel_mag") > 2.0) & (pl.col("gyro_mag") > 1.2),
            high_jerk_event=pl.col("jerk_mag") > 2.5,
        )
        .with_columns(
            anomaly_flag=pl.col("slip_detected") | pl.col("high_jerk_event"),
        )
    )

    return processed_df


def ingest_physical_ai_dataset(
    processed_df: pl.DataFrame,
    target_path: str = "data/04_feature/physical_ai.lance",
) -> str:
    """
    Writes the multi-modal robotics telemetry into Lance storage,
    enables stable row IDs, and constructs an IVF-PQ vector index on sensor embeddings.
    """
    dest = Path(target_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Convert Polars to Arrow Table
    arrow_table = processed_df.to_arrow()

    # Cast vector column to fixed-size list for optimal Lance vector indexing
    embedding_dim = len(processed_df["raw_sensor_embedding"][0])
    vector_field = pa.field(
        "raw_sensor_embedding",
        pa.list_(pa.float32(), list_size=embedding_dim),
    )
    schema = arrow_table.schema
    field_idx = schema.get_field_index("raw_sensor_embedding")
    schema = schema.set(field_idx, vector_field)
    arrow_table = arrow_table.cast(schema)

    # Write Lance dataset with overwrite mode
    ds = lance.write_dataset(
        arrow_table,
        str(dest),
        mode="overwrite",
        enable_stable_row_ids=True,
        max_rows_per_file=50_000,
    )

    # Build IVF-PQ Index on sensor embeddings if row count allows (IVF-PQ requires >= 256 rows for 256 PQ centroids)
    if ds.count_rows() >= 256:
        num_partitions = min(4, max(1, ds.count_rows() // 100))
        num_sub_vectors = min(4, max(1, embedding_dim // 4))
        ds.create_index(
            column="raw_sensor_embedding",
            index_type="IVF_PQ",
            metric="cosine",
            num_partitions=num_partitions,
            num_sub_vectors=num_sub_vectors,
            replace=True,
        )

    return str(dest)


def mine_physical_ai_events(
    lance_path: str = "data/04_feature/physical_ai.lance",
    filter_expr: str = "slip_detected = true",
    limit: int = 5,
) -> dict[str, Any]:
    """
    Performs hybrid multimodal data mining over Physical AI telemetry:
    Applies pushdown SQL filters (e.g. slip_detected, high_jerk) combined with
    vector search or columnar projection.
    """
    ds = lance.dataset(lance_path)
    scanner = ds.scanner(
        filter=filter_expr,
        columns=[
            "episode_id",
            "step_id",
            "timestamp_ns",
            "accel_mag",
            "gyro_mag",
            "jerk_mag",
            "slip_detected",
            "anomaly_flag",
            "raw_sensor_embedding",
        ],
        limit=limit,
    )

    tbl = scanner.to_table()
    matches = tbl.to_pylist()

    result = {
        "query_filter": filter_expr,
        "total_matched_samples": len(matches),
        "episodes_affected": sorted(list({m["episode_id"] for m in matches})),
        "sample_events": [
            {
                "episode_id": m["episode_id"],
                "step_id": m["step_id"],
                "accel_mag": round(m["accel_mag"], 3),
                "jerk_mag": round(m["jerk_mag"], 3),
                "slip_detected": m["slip_detected"],
            }
            for m in matches[:5]
        ],
    }

    return result
