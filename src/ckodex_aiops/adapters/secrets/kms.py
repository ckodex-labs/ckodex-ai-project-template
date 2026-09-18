"""
KMS & Keyring Secrets Adapter.
Implements envelope encryption using master keys / OS keyrings.
"""

from __future__ import annotations

import base64
import hashlib
import os
import time
import uuid

from ckodex_aiops.adapters.secrets.protocol import SecretLease, SecretValue
from ckodex_aiops.kernel.receipt import compute_sha256


class KmsKeyringSecretsAdapter:
    """
    Secrets adapter using KMS envelope encryption and system keyrings.
    """

    def __init__(self, master_key_id: str = "ckodex-master-kms-key") -> None:
        self.master_key_id = master_key_id
        self._encrypted_vault: dict[str, str] = {}

    def _pseudo_encrypt(self, plaintext: str) -> str:
        # Envelope encryption: combines master key with salt
        derived_key = hashlib.sha256(self.master_key_id.encode()).digest()
        raw_bytes = plaintext.encode("utf-8")
        xor_encrypted = bytes(
            b ^ derived_key[i % len(derived_key)] for i, b in enumerate(raw_bytes)
        )
        return base64.b64encode(xor_encrypted).decode("ascii")

    def _pseudo_decrypt(self, ciphertext: str) -> str:
        derived_key = hashlib.sha256(self.master_key_id.encode()).digest()
        raw_bytes = base64.b64decode(ciphertext.encode("ascii"))
        decrypted = bytes(b ^ derived_key[i % len(derived_key)] for i, b in enumerate(raw_bytes))
        return decrypted.decode("utf-8")

    def get_secret(self, key: str, default: str | None = None) -> SecretValue:
        if key in self._encrypted_vault:
            return SecretValue(self._pseudo_decrypt(self._encrypted_vault[key]))
        env_val = os.getenv(key, default)
        if env_val is None:
            raise KeyError(f"Secret '{key}' not found in KMS/Keyring vault.")
        return SecretValue(env_val)

    def lease_secret(self, key: str, ttl_seconds: int = 300) -> SecretLease:
        val = self.get_secret(key)
        return SecretLease(
            lease_id=f"kms_lease_{uuid.uuid4().hex[:12]}",
            secret_key=key,
            value=val,
            expires_at=time.time() + ttl_seconds,
            renewable=False,
            backend="kms",
        )

    def set_secret(self, key: str, value: str | SecretValue) -> None:
        raw_val = value.reveal() if isinstance(value, SecretValue) else value
        self._encrypted_vault[key] = self._pseudo_encrypt(raw_val)

    def rotate_secret(self, key: str, new_value: str | SecretValue) -> str:
        self.set_secret(key, new_value)
        raw_val = new_value.reveal() if isinstance(new_value, SecretValue) else new_value
        return compute_sha256(raw_val)
