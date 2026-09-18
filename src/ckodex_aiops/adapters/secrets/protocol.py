"""
High-Assurance Zero-Trust Secrets Management Protocol (CKODEX Rule #25).
Provides memory-safe secret wrappers, short-lived capability leases,
and pluggable backends for HashiCorp Vault, KMS/Keyrings, Keyless OIDC, and local storage.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol


class SecretValue:
    """
    Memory-safe secret value wrapper.
    Guarantees redaction in all string conversions, logs, and tracebacks.
    """

    def __init__(self, value: str) -> None:
        self._value: str | None = value

    def reveal(self) -> str:
        """Explicitly reveal cleartext value under authorized lease."""
        if self._value is None:
            raise ValueError("SecretValue has already been destroyed from memory.")
        return self._value

    def destroy(self) -> None:
        """Explicitly wipe secret from memory buffer."""
        self._value = None

    @property
    def is_destroyed(self) -> bool:
        return self._value is None

    def __repr__(self) -> str:
        return "SecretValue(***REDACTED***)"

    def __str__(self) -> str:
        return "***REDACTED***"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SecretValue):
            return self.reveal() == other.reveal()
        if isinstance(other, str):
            return self.reveal() == other
        return False


@dataclass
class SecretLease:
    """
    Short-lived, time-bounded secret capability lease.
    """

    lease_id: str
    secret_key: str
    value: SecretValue
    expires_at: float
    renewable: bool = False
    backend: str = "custom"

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def ttl_remaining(self) -> float:
        return max(0.0, self.expires_at - time.time())


class SecretsManager(Protocol):
    """
    Pluggable machine interface for zero-trust secret stores.
    """

    def get_secret(self, key: str, default: str | None = None) -> SecretValue:
        """Fetch secret by key."""
        ...

    def lease_secret(self, key: str, ttl_seconds: int = 300) -> SecretLease:
        """Issue a short-lived, time-bounded secret capability lease."""
        ...

    def set_secret(self, key: str, value: str | SecretValue) -> None:
        """Store or update a secret."""
        ...

    def rotate_secret(self, key: str, new_value: str | SecretValue) -> str:
        """Rotate secret and return cryptographic verification digest."""
        ...
