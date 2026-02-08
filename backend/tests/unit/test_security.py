"""Unit tests for JWT and password security utilities."""

from datetime import timedelta
from unittest.mock import patch

import pytest

from app.core.exceptions import UnauthorizedError


@pytest.fixture(autouse=True)
def mock_settings():
    """Patch settings for all tests in this module."""
    from app.config import Settings

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///",
        REDIS_URL="redis://localhost:6379/15",
        RABBITMQ_URL="amqp://guest:guest@localhost:5672/",
        JWT_SECRET="test-secret",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRY_MINUTES=60,
        ANTHROPIC_API_KEY="test-key",
        ANTHROPIC_MODEL="claude-sonnet-4-20250514",
    )
    with patch("app.infrastructure.security.get_settings", return_value=settings):
        yield settings


class TestPasswordHashing:
    def test_hash_and_verify_correct_password(self):
        from app.infrastructure.security import hash_password, verify_password

        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        from app.infrastructure.security import hash_password, verify_password

        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_different_each_time(self):
        from app.infrastructure.security import hash_password

        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # Different salts


class TestJWT:
    def test_create_and_decode_token(self):
        from app.infrastructure.security import create_access_token, decode_access_token

        token = create_access_token(data={"sub": "user-123"})
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert "exp" in payload

    def test_decode_invalid_token_raises(self):
        from app.infrastructure.security import decode_access_token

        with pytest.raises(UnauthorizedError):
            decode_access_token("invalid.jwt.token")

    def test_custom_expiry(self):
        from app.infrastructure.security import create_access_token, decode_access_token

        token = create_access_token(
            data={"sub": "user-456"},
            expires_delta=timedelta(minutes=5),
        )
        payload = decode_access_token(token)
        assert payload["sub"] == "user-456"
