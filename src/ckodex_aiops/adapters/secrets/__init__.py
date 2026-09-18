"""
Zero-Trust Secrets Management Adapters (Rule #25).
"""

from ckodex_aiops.adapters.secrets.composite import CompositeSecretsManager
from ckodex_aiops.adapters.secrets.keyless import KeylessPassSecretsAdapter
from ckodex_aiops.adapters.secrets.kms import KmsKeyringSecretsAdapter
from ckodex_aiops.adapters.secrets.protocol import SecretLease, SecretsManager, SecretValue
from ckodex_aiops.adapters.secrets.vault import HashiCorpVaultSecretsAdapter

__all__ = [
    "SecretValue",
    "SecretLease",
    "SecretsManager",
    "HashiCorpVaultSecretsAdapter",
    "KmsKeyringSecretsAdapter",
    "KeylessPassSecretsAdapter",
    "CompositeSecretsManager",
]
