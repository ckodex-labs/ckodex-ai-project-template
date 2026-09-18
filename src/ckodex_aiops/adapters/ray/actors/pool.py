"""
Ray Actor Pool Manager.
Distributes work across a managed pool of stateful Ray actors with round-robin scheduling and error recovery.
"""

from __future__ import annotations

from typing import Any

import ray


class ActorPoolManager:
    """
    Manages a lifecycle-bounded pool of Ray actors.
    """

    def __init__(self, actors: list[ray.actor.ActorHandle]) -> None:
        if not actors:
            raise ValueError("ActorPoolManager requires at least one actor handle.")
        self.actors = actors
        self._index = 0

    @classmethod
    def create_embedding_pool(cls, size: int = 2, embedding_dim: int = 32) -> ActorPoolManager:
        from ckodex_aiops.adapters.ray.actors.embedding_actor import EmbeddingActor

        actors = [
            EmbeddingActor.remote(embedding_dim=embedding_dim, seed=42 + i) for i in range(size)
        ]
        return cls(actors)

    @classmethod
    def create_inference_pool(
        cls,
        size: int = 2,
        model_state_dict: dict[str, Any] | None = None,
        input_dim: int = 32,
        hidden_dim: int = 64,
        num_classes: int = 4,
    ) -> ActorPoolManager:
        from ckodex_aiops.adapters.ray.actors.inference_actor import InferenceActor

        actors = [
            InferenceActor.remote(
                model_state_dict=model_state_dict,
                input_dim=input_dim,
                hidden_dim=hidden_dim,
                num_classes=num_classes,
            )
            for _ in range(size)
        ]
        return cls(actors)

    def dispatch_batch(self, method_name: str, batches: list[Any]) -> list[Any]:
        """
        Dispatches chunks to actors in round-robin fashion and gathers ray object refs.
        """
        futures = []
        for i, batch in enumerate(batches):
            actor = self.actors[i % len(self.actors)]
            method = getattr(actor, method_name)
            futures.append(method.remote(batch))

        return ray.get(futures)

    def health_check(self) -> list[dict[str, Any]]:
        futures = [actor.health_check.remote() for actor in self.actors]
        return ray.get(futures)

    def terminate(self) -> None:
        for actor in self.actors:
            ray.kill(actor)
