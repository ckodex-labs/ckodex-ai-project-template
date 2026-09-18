"""
Project Settings for Kedro.
Registers custom hooks, catalog paths, and environment settings.
"""

from ckodex_aiops.hooks.evidence_hook import EvidenceHook
from ckodex_aiops.hooks.ray_lifecycle import RayLifecycleHook

# Instantiated hooks registered with Kedro
HOOKS = (
    RayLifecycleHook(auto_shutdown=False),
    EvidenceHook(),
)

# Configuration directory source
CONF_SOURCE = "conf"
