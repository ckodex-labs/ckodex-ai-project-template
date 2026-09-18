"""
Stateful Ray Actors for CKODEX AI Platform.
"""

from ckodex_aiops.adapters.ray.actors.embedding_actor import EmbeddingActor
from ckodex_aiops.adapters.ray.actors.inference_actor import InferenceActor
from ckodex_aiops.adapters.ray.actors.pool import ActorPoolManager

__all__ = ["EmbeddingActor", "InferenceActor", "ActorPoolManager"]
