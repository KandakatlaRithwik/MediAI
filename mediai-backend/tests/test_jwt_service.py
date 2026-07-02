"""Tests for JWTService and PasswordService - no database required."""

import time

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.services.jwt_service import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE, JWTService
from app.services.password_service import PasswordService


def test_create_and_decode_access_token():
    service = JWTService()
    token = service.create_access_token(subject="user-uuid-123", role="PATIENT")
    payload = service.decode_token(token)
    assert payload["sub"] == "user-uuid-123"
    assert payload["role"] == "PATIENT"
    assert payload["type"] == ACCESS_TOKEN_TYPE


def test_create_and_decode_refresh_token():
    service = JWTService()
    token = service.create_refresh_token(subject="user-uuid-456")
    payload = service.decode_token(token)
    assert payload["sub"] == "user-uuid-456"
    assert payload["type"] == REFRESH_TOKEN_TYPE


def test_decode_invalid_token_raises_authentication_error():
    service = JWTService()
    with pytest.raises(AuthenticationError):
        service.decode_token("not.a.valid.token")


def test_decode_expired_token_raises_authentication_error():
    settings = get_settings()
    # Build a token that already expired 10 seconds ago.
    payload = {"sub": "user-uuid-789", "type": ACCESS_TOKEN_TYPE, "exp": int(time.time()) - 10}
    expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    service = JWTService()
    with pytest.raises(AuthenticationError):
        service.decode_token(expired_token)


def test_decode_token_with_wrong_secret_raises_authentication_error():
    settings = get_settings()
    payload = {"sub": "user-uuid-000", "type": ACCESS_TOKEN_TYPE, "exp": int(time.time()) + 3600}
    token_signed_with_wrong_secret = jwt.encode(payload, "a-completely-different-secret", algorithm=settings.JWT_ALGORITHM)

    service = JWTService()
    with pytest.raises(AuthenticationError):
        service.decode_token(token_signed_with_wrong_secret)


def test_access_and_refresh_tokens_for_same_subject_differ():
    service = JWTService()
    access = service.create_access_token(subject="same-user", role="PATIENT")
    refresh = service.create_refresh_token(subject="same-user")
    assert access != refresh


def test_password_hash_and_verify_roundtrip():
    service = PasswordService()
    hashed = service.hash_password("my-secret-password")
    assert hashed != "my-secret-password"
    assert service.verify_password("my-secret-password", hashed) is True


def test_password_verify_rejects_wrong_password():
    service = PasswordService()
    hashed = service.hash_password("correct-password")
    assert service.verify_password("wrong-password", hashed) is False


def test_password_hashes_are_salted_and_unique():
    service = PasswordService()
    hash1 = service.hash_password("same-password")
    hash2 = service.hash_password("same-password")
    assert hash1 != hash2  # different salts
    assert service.verify_password("same-password", hash1) is True
    assert service.verify_password("same-password", hash2) is True
