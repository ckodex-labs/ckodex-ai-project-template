"""
Compliance & Attestation Adapters (CKODEX Rule #10, #39).
Implements In-toto SLSA v1.0 Provenance and NIST SP 800-53 OSCAL generation.
"""

from ckodex_aiops.adapters.compliance.intoto import IntotoProvenanceAttestor
from ckodex_aiops.adapters.compliance.oscal import OscalComplianceGenerator

__all__ = ["IntotoProvenanceAttestor", "OscalComplianceGenerator"]
