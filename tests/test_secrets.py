"""Tests for Zero-Trust Secrets Management Abstraction.
Validates memory-safe SecretValue redaction, capability leases, and backend adapters.
"""

from __future__ import annotations

import time

import pytest

from ckodex_aiops.adapters.secrets.composite import CompositeSecretsManager
from ckodex_aiops.adapters.secrets.keyless import KeylessPassSecretsAdapter
from ckodex_aiops.adapters.secrets.kms import KmsKeyringSecretsAdapter
from ckodex_aiops.adapters.secrets.protocol import SecretLease, SecretValue
from ckodex_aiops.adapters.secrets.vault import HashiCorpVaultSecretsAdapter


def test_secret_value_redaction_and_destruction():
    """SecretValue must never leak raw values via str() or repr(), and must support memory wiping."""
    raw = "super-secret-production-token-12345"
    sec = SecretValue(raw)

    # Invariant: str and repr must be redacted
    assert str(sec) == "***REDACTED***"
    assert repr(sec) == "SecretValue(***REDACTED***)"
    assert raw not in str(sec)
    assert raw not in repr(sec)

    # Invariant: reveal() yields raw token
    assert sec.reveal() == raw

    # Invariant: destroy() wipes raw secret and forbids subsequent access
    sec.destroy()
    with pytest.raises(ValueError, match="destroyed"):
        sec.reveal()
    assert sec.is_destroyed is True


def test_secret_lease_ttl_and_expiry():
    """SecretLease must strictly observe temporal capability boundaries."""
    sec = SecretValue("ephemeral-key")
    now = time.time()
    lease = SecretLease(
        lease_id="lease-abc-123",
        secret_key="vault/db/creds",
        value=sec,
        expires_at=now + 10.0,
        renewable=False,
        backend="vault",
    )

    assert not lease.is_expired()
    assert lease.ttl_remaining() > 0.0
    assert lease.value.reveal() == "ephemeral-key"

    # Expired lease
    expired_lease = SecretLease(
        lease_id="lease-expired",
        secret_key="vault/db/creds",
        value=sec,
        expires_at=now - 10.0,
        renewable=False,
        backend="vault",
    )
    assert expired_lease.is_expired()
    assert expired_lease.ttl_remaining() == 0.0


def test_hashicorp_vault_adapter():
    """HashiCorpVaultSecretsAdapter must store, retrieve, and issue capability leases."""
    vault = HashiCorpVaultSecretsAdapter(
        vault_addr="http://127.0.0.1:8200", vault_token="s.mock-token"
    )
    vault.set_secret("aiops/storage/lance", "s3-access-key-999")

    # Fetch secret directly
    val = vault.get_secret("aiops/storage/lance")
    assert val.reveal() == "s3-access-key-999"

    # Lease secret
    lease = vault.lease_secret("aiops/storage/lance", ttl_seconds=300)
    assert lease.backend == "vault"
    assert lease.value.reveal() == "s3-access-key-999"
    assert not lease.is_expired()

    # Secret rotation emits cryptographic receipt
    digest = vault.rotate_secret("aiops/storage/lance", "s3-access-key-1000")
    assert len(digest) == 64
    assert vault.get_secret("aiops/storage/lance").reveal() == "s3-access-key-1000"

    # Non-existent secret raises KeyError
    with pytest.raises(KeyError):
        vault.get_secret("non/existent/key/1234")


def test_kms_keyring_adapter():
    """KmsKeyringSecretsAdapter must envelope-encrypt secrets and handle rotation."""
    kms = KmsKeyringSecretsAdapter(master_key_id="projects/prod/locations/global/keyRings/aiops")
    kms.set_secret("models/weights/hf_token", "hf_api_token_value_abc")

    # Decrypt and reveal
    val = kms.get_secret("models/weights/hf_token")
    assert val.reveal() == "hf_api_token_value_abc"

    # Lease
    lease = kms.lease_secret("models/weights/hf_token")
    assert lease.backend == "kms"
    assert lease.value.reveal() == "hf_api_token_value_abc"

    # Rotate
    digest = kms.rotate_secret("models/weights/hf_token", "hf_api_token_value_xyz")
    assert len(digest) == 64
    assert kms.get_secret("models/weights/hf_token").reveal() == "hf_api_token_value_xyz"


def test_keyless_pass_adapter(monkeypatch):
    """KeylessPassSecretsAdapter must mint short-lived tokens backed by ambient OIDC claims."""
    monkeypatch.setenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "mock-ambient-oidc-jwt-token-string")
    keyless = KeylessPassSecretsAdapter(oidc_audience="ckodex.cfyd.ai")

    lease = keyless.lease_secret("workload/identity/ray-cluster")
    assert lease.backend == "keyless"
    assert not lease.is_expired()
    assert lease.value.reveal() == "mock-ambient-oidc-jwt-token-string"


def test_composite_secrets_manager():
    """CompositeSecretsManager must query backends in priority order and fallback gracefully."""
    vault = HashiCorpVaultSecretsAdapter(vault_addr="http://127.0.0.1:8200")
    kms = KmsKeyringSecretsAdapter(master_key_id="test-keyring")

    vault.set_secret("shared/token", "vault-priority-token")
    kms.set_secret("shared/token", "kms-fallback-token")
    kms.set_secret("kms/only", "kms-exclusive-token")

    mgr = CompositeSecretsManager(providers=[vault, kms])

    # Resolves from Vault (first priority)
    val1 = mgr.get_secret("shared/token")
    assert val1.reveal() == "vault-priority-token"

    # Falls back to KMS
    val2 = mgr.get_secret("kms/only")
    assert val2.reveal() == "kms-exclusive-token"

    # Leases also follow fallback
    lease = mgr.lease_secret("kms/only")
    assert lease.backend == "kms"
    assert lease.value.reveal() == "kms-exclusive-token"

    # Missing from all
    with pytest.raises(KeyError, match="could not be resolved"):
        mgr.get_secret("nowhere/found")
