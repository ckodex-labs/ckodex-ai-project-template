"""
Project Settings for Kedro.
Registers custom hooks, catalog paths, and environment settings.
"""

from ckodex_aiops.hooks.authority_admission import AuthorityAdmissionHook
from ckodex_aiops.hooks.data_integrity import DataIntegrityHook
from ckodex_aiops.hooks.ray_lifecycle import RayLifecycleHook
from ckodex_aiops.hooks.resilience_circuit import ResilienceCircuitBreakerHook
from ckodex_aiops.hooks.traceability_evidence import TraceabilityEvidenceHook

# Instantiated hooks registered with Kedro
HOOKS = (
    AuthorityAdmissionHook(strict_mode=True),
    RayLifecycleHook(auto_shutdown=False),
    DataIntegrityHook(fail_on_corruption=True),
    ResilienceCircuitBreakerHook(),
    TraceabilityEvidenceHook(),
)

# Configuration directory source
CONF_SOURCE = "conf"
