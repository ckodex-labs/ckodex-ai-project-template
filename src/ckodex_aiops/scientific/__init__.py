"""
CKODEX Scientific Kernel SDK.
Public interface for zero-boilerplate scientific node wrapping,
native data connectors (FASTA, PDB, Lance), and cryptographic asset offboarding.
"""

from __future__ import annotations

from ckodex_aiops.scientific.connectors import (
    IngestionManifest,
    ScientificDataConnector,
)
from ckodex_aiops.scientific.decorators import (
    ScientificExecutionProof,
    scientific_node,
)
from ckodex_aiops.scientific.tombstone import (
    AssetTombstoningEngine,
    DecommissionCertificate,
)

__all__ = [
    "scientific_node",
    "ScientificExecutionProof",
    "ScientificDataConnector",
    "IngestionManifest",
    "AssetTombstoningEngine",
    "DecommissionCertificate",
]
