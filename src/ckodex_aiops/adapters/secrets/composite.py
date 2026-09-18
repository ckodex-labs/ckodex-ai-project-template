"""
Composite Secrets Manager.
Layered zero-trust secrets resolution: Vault -> KMS/Keyring -> Keyless -> Environment.
"""

from __future__ import annotations

from ckodex_aiops.adapters.secrets.keyless import KeylessPassSecretsAdapter
from ckodex_aiops.adapters.secrets.kms import KmsKeyringSecretsAdapter
from ckodex_aiops.adapters.secrets.protocol import SecretLease, SecretsManager, SecretValue
from ckodex_aiops.adapters.secrets.vault import HashiCorpVaultSecretsAdapter


class CompositeSecretsManager:
    """
    Tiered secrets manager with automatic fallback across providers.
    """

    def __init__(self, providers: list[SecretsManager] | None = None) -> None:
        if providers is None:
            self.providers: list[SecretsManager] = [
                HashiCorpVaultSecretsAdapter(),
                KmsKeyringSecretsAdapter(),
                KeylessPassSecretsAdapter(),
            ]
        else:
            self.providers = providers

    def get_secret(self, key: str, default: str | None = None) -> SecretValue:
        for provider in self.providers:
            try:
                return provider.get_secret(key)
            except Exception:
                continue
        if default is not None:
            return SecretValue(default)
        raise KeyError(
            f"Secret '{key}' could not be resolved across any configured secret provider."
        )

    def lease_secret(self, key: str, ttl_seconds: int = 300) -> SecretLease:
        for provider in self.providers:
            try:
                return provider.lease_secret(key, ttl_seconds=ttl_seconds)
            except Exception:
                continue
        raise KeyError(f"Could not acquire secret capability lease for '{key}'.")

    def set_secret(self, key: str, value: str | SecretValue) -> None:
        if self.providers:
            self.providers[0].set_secret(key, value)

    def rotate_secret(self, key: str, new_value: str | SecretValue) -> str:
        if self.providers:
            return self.providers[0].rotate_secret(key, new_value)
        return ""
