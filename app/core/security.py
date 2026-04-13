"""JWT token handling, password hashing, AES encryption."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def _get_jwt_key_and_algo() -> tuple[str, str]:
    """Return (key, algorithm) for signing."""
    private_key = settings.jwt_private_key
    if private_key:
        return private_key, "RS256"
    return settings.jwt_secret, "HS256"


def _get_jwt_verify_key_and_algo() -> tuple[str, str]:
    """Return (key, algorithm) for verification."""
    public_key = settings.jwt_public_key
    if public_key:
        return public_key, "RS256"
    return settings.jwt_secret, "HS256"


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    key, algo = _get_jwt_key_and_algo()
    return jwt.encode(to_encode, key, algorithm=algo)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    key, algo = _get_jwt_key_and_algo()
    return jwt.encode(to_encode, key, algorithm=algo)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises JWTError on failure."""
    key, algo = _get_jwt_verify_key_and_algo()
    return jwt.decode(token, key, algorithms=[algo])


# ---------------------------------------------------------------------------
# AES-256-CBC encryption for stored secrets (API keys, passwords)
# ---------------------------------------------------------------------------

def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode()).digest()


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string using AES-256-CBC. Returns 'iv_hex:ciphertext_hex'."""
    key = _derive_key(settings.config_encryption_key)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    # PKCS7 padding
    pad_len = 16 - (len(plaintext.encode()) % 16)
    padded = plaintext.encode() + bytes([pad_len] * pad_len)
    ct = encryptor.update(padded) + encryptor.finalize()
    return f"{iv.hex()}:{ct.hex()}"


def decrypt_value(encrypted: str) -> str:
    """Decrypt an 'iv_hex:ciphertext_hex' string."""
    key = _derive_key(settings.config_encryption_key)
    iv_hex, ct_hex = encrypted.split(":")
    iv = bytes.fromhex(iv_hex)
    ct = bytes.fromhex(ct_hex)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    pad_len = padded[-1]
    return padded[:-pad_len].decode()
