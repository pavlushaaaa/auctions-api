"""Test security and authentication utilities"""
import pytest
from datetime import timedelta


def test_password_hashing():
    from app.core.security import get_password_hash, verify_password

    password = "test_password123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_verify_wrong_password():
    from app.core.security import get_password_hash, verify_password

    password = "correct_password"
    hashed = get_password_hash(password)

    assert not verify_password("incorrect_password", hashed)


def test_create_access_token():
    from app.core.security import create_access_token

    data = {"sub": "test@example.com", "role": "participant"}
    token = create_access_token(data=data)

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token():
    from app.core.security import create_access_token, decode_access_token

    data = {"sub": "test@example.com", "role": "participant"}
    token = create_access_token(data=data)

    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "test@example.com"
    assert decoded["role"] == "participant"


def test_decode_invalid_token():
    from app.core.security import decode_access_token

    invalid_token = "invalid.token.here"
    decoded = decode_access_token(invalid_token)

    assert decoded is None


def test_token_expiration():
    from app.core.security import create_access_token, decode_access_token
    import time

    data = {"sub": "test@example.com"}
    token = create_access_token(data=data, expires_delta=timedelta(seconds=1))

    time.sleep(2)

    decoded = decode_access_token(token)
    assert decoded is None


def test_multiple_password_hashes_different():
    from app.core.security import get_password_hash

    password = "same_password"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2
