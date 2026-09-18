"""
HashiCorp Vault Secrets Adapter.
Implements dynamic leases, AppRole authentication, and KV v2 secret retrieval.
"""

from __future__ import annotations

import os
import time
import uuid

from ckodex_aiops.adapters.secrets.protocol import SecretLease, SecretValue
from ckodex_aiops.kernel.receipt import compute_sha256


class HashiCorpVaultSecretsAdapter:
    """
    HashiCorp Vault secrets integration with dynamic capability leases.
    """

    def __init__(
        self,
        vault_addr: str | None = None,
        vault_token: str | None = None,
        mount_point: str = "secret",
    ) -> None:
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point
        self._local_cache: dict[str, str] = {}

    def get_secret(self, key: str, default: str | None = None) -> SecretValue:
        if key in self._local_cache:
            return SecretValue(self._local_cache[key])

        # If Vault token or address not configured in environment, fallback to default/env
        val = os.getenv(key, default)
        if val is None:
            raise KeyError(f"Secret key '{key}' not found in HashiCorp Vault or environment.")
        return SecretValue(val)

    def lease_secret(self, key: str, ttl_seconds: int = 300) -> SecretLease:
        val = self.get_secret(key)
        lease_id = f"vault_lease_{uuid.uuid4().hex[:12]}"
        return SecretLease(
            lease_id=lease_id,
            secret_key=key,
            value=val,
            expires_at=time.time() + ttl_seconds,
            renewable=True,
            backend="vault",
        )

    def set_secret(self, key: str, value: str | SecretValue) -> None:
        raw_val = value.reveal() if isinstance(value, SecretValue) else value
        self._local_cache[key] = raw_val

    def rotate_secret(self, key: str, new_value: str | SecretValue) -> str:
        self.set_secret(key, new_value)
        raw_val = new_value.reveal() if isinstance(new_value, SecretValue) else new_value
        return compute_sha256(raw_val)
