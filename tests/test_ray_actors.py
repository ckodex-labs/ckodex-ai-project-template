"""
Unit tests for Ray Actors & Actor Pool.
"""

import pytest
import ray

from ckodex_aiops.adapters.ray.actors.embedding_actor import EmbeddingActor
from ckodex_aiops.adapters.ray.actors.inference_actor import InferenceActor
from ckodex_aiops.adapters.ray.actors.pool import ActorPoolManager
from ckodex_aiops.adapters.ray.runtime import RayRuntimeManager


@pytest.fixture(scope="module")
def init_ray():
    RayRuntimeManager.initialize()
    yield
    # Keep session for subsequent tests or shutdown


def test_embedding_actor(init_ray):
    from typing import Any

    actor_cls: Any = EmbeddingActor
    actor = actor_cls.remote(embedding_dim=16)
    features = [[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]]

    future = actor.generate_embeddings.remote(features)
    embeddings = ray.get(future)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 16

    health = ray.get(actor.health_check.remote())
    assert health["status"] == "HEALTHY"
    assert health["total_processed"] == 2

    ray.kill(actor)


def test_inference_actor(init_ray):
    from typing import Any

    actor_cls: Any = InferenceActor
    actor = actor_cls.remote(input_dim=16, num_classes=3, device="cpu")
    features = [[0.1] * 16, [0.9] * 16]

    res = ray.get(actor.predict_batch.remote(features))
    assert "predictions" in res
    assert len(res["predictions"]) == 2
    assert "probabilities" in res
    assert len(res["probabilities"][0]) == 3

    health = ray.get(actor.health_check.remote())
    assert health["status"] == "HEALTHY"
    assert health["total_inferences"] == 2

    ray.kill(actor)


def test_actor_pool_manager(init_ray):
    pool = ActorPoolManager.create_embedding_pool(size=2, embedding_dim=16)
    batches = [
        [[1.0, 1.0, 1.0, 1.0], [2.0, 2.0, 2.0, 2.0]],
        [[3.0, 3.0, 3.0, 3.0], [4.0, 4.0, 4.0, 4.0]],
    ]
    results = pool.dispatch_batch("generate_embeddings", batches)
    assert len(results) == 2
    assert len(results[0]) == 2
    assert len(results[1]) == 2

    pool.terminate()
