"""
Role-based access control dependencies (Module 4).

Three dependencies, for three distinct needs:

  - get_current_user: REQUIRES a valid access token. Used by endpoints that
    cannot function at all without an authenticated user (/auth/me,
    /history/*, /dashboard/summary).

  - get_optional_current_user: returns the user if a valid token is
    present, or None otherwise - never raises for a missing/invalid token.
    Used by endpoints that must keep working exactly as before for
    anonymous callers (/ask, /symptom-checker, /analyze-report), but gain
    extra functionality (history-aware RAG, automatic history saving) when
    a valid token IS present.

    Deliberately does NOT depend on `Depends(get_db)`: if no token is
    provided at all, this returns None without ever touching the database,
    so those endpoints keep working unmodified even when Postgres is
    completely unavailable - exactly the "DO NOT modify working
    functionality unnecessarily" requirement. A DB session is only opened
    if a token is actually present, since at that point the caller is
    explicitly asking to be authenticated.

  - require_role(*roles): builds on get_current_user, additionally
    rejecting users whose role isn't in the allowed set.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.database.connection import SessionLocal, get_db
from app.database.models.user import User, UserRole
from app.services.jwt_service import ACCESS_TOKEN_TYPE, JWTService

logger = logging.getLogger("auth")

# auto_error=False: a missing Authorization header should be handled by our
# own logic (raise for required auth, return None for optional auth) rather
# than FastAPI's default 403 with a generic message.
_bearer_scheme = HTTPBearer(auto_error=False)


def _resolve_user_from_token(token: str, db: Session) -> User:
    jwt_service = JWTService()
    payload = jwt_service.decode_token(token)

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise AuthenticationError("An access token is required for this request.")

    user = db.query(User).filter(User.uuid == payload.get("sub")).first()
    if not user:
        raise AuthenticationError("User not found.")
    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid access token; raise AuthenticationError otherwise."""
    if credentials is None:
        raise AuthenticationError("Not authenticated. A valid Bearer token is required.")
    return _resolve_user_from_token(credentials.credentials, db)


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[User]:
    """Return the authenticated user if a valid token is present, else None.
    Never raises - and never touches the database when no token is given."""
    if credentials is None:
        return None

    if SessionLocal is None:
        logger.warning("Bearer token provided but database is unavailable; treating request as anonymous.")
        return None

    db = SessionLocal()
    try:
        return _resolve_user_from_token(credentials.credentials, db)
    except AuthenticationError as exc:
        logger.info("Optional auth: invalid/expired token, falling back to anonymous (%s)", exc.message)
        return None
    finally:
        db.close()


def require_role(*allowed_roles: UserRole):
    """Dependency factory: require an authenticated user whose role is one of `allowed_roles`."""

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            allowed_names = [role.value for role in allowed_roles]
            raise AuthorizationError(
                f"This action requires one of the following roles: {allowed_names}."
            )
        return current_user

    return _dependency


def resolve_target_patient(
    requested_patient_uuid: Optional[str],
    current_user: User,
    db: Session,
) -> User:
    """Resolve which patient's records the current user is allowed to view.

    - No `requested_patient_uuid` -> always resolves to the current user's
      own records (works for every role).
    - A PATIENT requesting a different patient's uuid -> denied. A patient
      may only ever view their own history.
    - A DOCTOR or ADMIN may request any patient's uuid. The spec describes
      doctors as scoped to "assigned patients", but no doctor-patient
      assignment table was part of the requested schema, so this is
      simplified to "any DOCTOR or ADMIN may look up any patient by uuid" -
      a deliberate, documented simplification (see README) rather than an
      oversight; a `doctor_patient_assignments` table is a natural follow-up.
    """
    if requested_patient_uuid is None or requested_patient_uuid == str(current_user.uuid):
        return current_user

    if current_user.role == UserRole.PATIENT:
        raise AuthorizationError("Patients may only access their own records.")

    target_user = db.query(User).filter(User.uuid == requested_patient_uuid).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Requested patient not found.")
    return target_user
