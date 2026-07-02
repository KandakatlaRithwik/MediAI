"""
JWT access/refresh token generation and validation (Module 4), using
python-jose.

The token subject (`sub`) is the user's public UUID, never the internal
sequential `id` - so decoding a token never leaks how many users exist or
which row a given user occupies.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

logger = logging.getLogger("auth")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class JWTService:
    def __init__(self) -> None:
        settings = get_settings()
        self._secret_key = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._access_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def _create_token(self, subject: str, token_type: str, expires_delta: timedelta, **extra_claims: Any) -> str:
        now = datetime.now(timezone.utc)
        payload: Dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            # jti: unique per token, so two tokens issued for the same user
            # within the same second (e.g. immediate login -> refresh) are
            # still distinct strings, not just distinct in theory. Also a
            # standard JWT field that would anchor future revocation support.
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + expires_delta,
            **extra_claims,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_access_token(self, subject: str, role: str) -> str:
        return self._create_token(
            subject, ACCESS_TOKEN_TYPE, timedelta(minutes=self._access_expire_minutes), role=role
        )

    def create_refresh_token(self, subject: str) -> str:
        return self._create_token(subject, REFRESH_TOKEN_TYPE, timedelta(days=self._refresh_expire_days))

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT, raising AuthenticationError on any failure
        (expired, malformed, wrong signature) rather than leaking the
        underlying jose exception type to callers."""
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError as exc:
            logger.warning("Token validation failed: %s", exc)
            raise AuthenticationError("Invalid or expired token.") from exc
