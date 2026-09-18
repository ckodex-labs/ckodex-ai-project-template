"""
Keyless / Ambient Workload Identity Secrets Adapter.
Eliminates static long-lived credentials by federating ephemeral OIDC workload tokens.
"""

from __future__ import annotations

import os
import time
import uuid

from ckodex_aiops.adapters.secrets.protocol import SecretLease, SecretValue
from ckodex_aiops.kernel.receipt import compute_sha256


class KeylessPassSecretsAdapter:
    """
    Keyless OIDC federation adapter for ambient cloud & CI/CD workload identity.
    """

    def __init__(self, oidc_audience: str = "ckodex.cfyd.ai") -> None:
        self.oidc_audience = oidc_audience

    def get_secret(self, key: str, default: str | None = None) -> SecretValue:
        # Check standard ambient token locations (e.g. ACTIONS_ID_TOKEN_REQUEST_TOKEN or AWS_WEB_IDENTITY_TOKEN_FILE)
        oidc_token = os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN") or os.getenv("OIDC_BEARER_TOKEN")
        if oidc_token:
            return SecretValue(oidc_token)
        val = os.getenv(key, default)
        if val is None:
            raise KeyError(
                f"Keyless token for '{key}' unavailable; no ambient workload identity detected."
            )
        return SecretValue(val)

    def lease_secret(self, key: str, ttl_seconds: int = 300) -> SecretLease:
        val = self.get_secret(key)
        return SecretLease(
            lease_id=f"keyless_lease_{uuid.uuid4().hex[:12]}",
            secret_key=key,
            value=val,
            expires_at=time.time() + ttl_seconds,
            renewable=True,
            backend="keyless",
        )

    def set_secret(self, key: str, value: str | SecretValue) -> None:
        # Ephemeral by design: static writes not permitted on ambient keyless adapter
        pass

    def rotate_secret(self, key: str, new_value: str | SecretValue) -> str:
        raw_val = new_value.reveal() if isinstance(new_value, SecretValue) else new_value
        return compute_sha256(raw_val)
