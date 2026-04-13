"""Tests for security module: JWT, password hashing, AES encryption."""

import pytest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_value,
    decrypt_value,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("secure123")
        assert verify_password("secure123", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("secure123")
        assert not verify_password("wrong", hashed)

    def test_different_passwords_different_hashes(self):
        h1 = hash_password("pass1")
        h2 = hash_password("pass2")
        assert h1 != h2

    def test_same_password_different_hashes(self):
        """bcrypt uses random salt, so same password -> different hash."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        assert verify_password("same", h1)
        assert verify_password("same", h2)


class TestJWT:
    def test_access_token(self):
        token = create_access_token({"sub": "user-1", "role": "agent_l1"})
        payload = decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["type"] == "access"

    def test_refresh_token(self):
        token = create_refresh_token({"sub": "user-1"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_invalid_token_raises(self):
        from jose import JWTError
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_token_contains_custom_claims(self):
        token = create_access_token({
            "sub": "u1", "tenant_id": "t1", "email": "a@b.com", "role": "manager",
        })
        payload = decode_token(token)
        assert payload["tenant_id"] == "t1"
        assert payload["email"] == "a@b.com"
        assert payload["role"] == "manager"


class TestAESEncryption:
    def test_encrypt_decrypt(self):
        secret = "sk-ant-api-key-very-secret"
        encrypted = encrypt_value(secret)
        decrypted = decrypt_value(encrypted)
        assert decrypted == secret

    def test_random_iv(self):
        """Same plaintext should produce different ciphertext."""
        enc1 = encrypt_value("same")
        enc2 = encrypt_value("same")
        assert enc1 != enc2

    def test_format(self):
        encrypted = encrypt_value("test")
        assert ":" in encrypted
        iv, ct = encrypted.split(":")
        assert len(iv) == 32  # 16 bytes hex
        assert len(ct) > 0

    def test_unicode(self):
        secret = "Türkçe-şifre-ğüö"
        assert decrypt_value(encrypt_value(secret)) == secret

    def test_long_value(self):
        secret = "x" * 10000
        assert decrypt_value(encrypt_value(secret)) == secret
