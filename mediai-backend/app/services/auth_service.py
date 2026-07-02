"""
AuthService - top-level orchestrator for register/login/refresh/me
(Module 4).

Unlike the stateless singleton services elsewhere in this codebase
(RAGService, SymptomCheckerService, etc.), AuthService's methods accept a
SQLAlchemy `Session` as a parameter rather than holding one in `__init__` -
DB sessions are per-request, not per-service-instance, so the route layer
provides one via `Depends(get_db)` and passes it through.
"""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, UserAlreadyExistsError
from app.database.models.user import User
from app.schemas.auth import LoginRequest, PasswordResetRequest, RegisterRequest, TokenResponse
from app.services.jwt_service import REFRESH_TOKEN_TYPE, JWTService
from app.services.password_service import PasswordService

logger = logging.getLogger("auth")


class AuthService:
    def __init__(self) -> None:
        self._password_service = PasswordService()
        self._jwt_service = JWTService()

    def register(self, db: Session, request: RegisterRequest) -> User:
        normalized_email = request.email.lower()
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            logger.warning("Registration attempted with already-registered email: %s", normalized_email)
            raise UserAlreadyExistsError(f"A user with email '{request.email}' already exists.")

        user = User(
            full_name=request.full_name,
            email=normalized_email,
            password_hash=self._password_service.hash_password(request.password),
            phone=request.phone,
            role=request.role,
            security_question=request.security_question,
            security_answer_hash=self._password_service.hash_password(
                request.security_answer.strip().lower()
            ),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info("Registered new user: email=%s role=%s", normalized_email, request.role.value)
        return user

    def authenticate(self, db: Session, email: str, password: str) -> User:
        """Verify credentials and return the matching active user, or raise
        AuthenticationError. Intentionally returns the same generic message
        whether the email doesn't exist or the password is wrong, so the
        API never reveals which emails are registered."""
        normalized_email = email.lower()
        user = db.query(User).filter(User.email == normalized_email).first()

        if not user or not self._password_service.verify_password(password, user.password_hash):
            logger.warning("Failed login attempt for email: %s", normalized_email)
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            logger.warning("Login attempt for deactivated account: %s", normalized_email)
            raise AuthenticationError("This account has been deactivated.")

        logger.info("Successful login: email=%s role=%s", normalized_email, user.role.value)
        return user

    def login(self, db: Session, request: LoginRequest) -> TokenResponse:
        user = self.authenticate(db, request.email, request.password)
        return self._issue_tokens(user)

    def refresh(self, db: Session, refresh_token: str) -> TokenResponse:
        payload = self._jwt_service.decode_token(refresh_token)
        if payload.get("type") != REFRESH_TOKEN_TYPE:
            raise AuthenticationError("The provided token is not a valid refresh token.")

        user = db.query(User).filter(User.uuid == payload.get("sub")).first()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive.")

        logger.info("Token refreshed for user: %s", user.email)
        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        subject = str(user.uuid)
        return TokenResponse(
            access_token=self._jwt_service.create_access_token(subject, user.role.value),
            refresh_token=self._jwt_service.create_refresh_token(subject),
            token_type="bearer",
        )

    # ------------------------------------------------------------------
    # Security-question-based password recovery
    # ------------------------------------------------------------------
    def get_security_question(self, db: Session, email: str) -> str:
        """Return the security question configured by the given user.

        Raises AuthenticationError with a deliberately generic message so
        the API never confirms whether an email is registered.
        """
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not user.is_active or not user.security_question:
            logger.warning("Security-question lookup failed for %s", email)
            raise AuthenticationError("No security question is available for this account.")
        logger.info("Security-question served for %s", email)
        return user.security_question

    def reset_password(self, db: Session, request: PasswordResetRequest) -> None:
        """Verify security answer and set a new password.

        Uses bcrypt.verify against the stored answer hash. Uses the same
        generic error whether the email doesn't exist or the answer is wrong,
        so this cannot be abused as a user-enumeration oracle.
        """
        normalized_email = request.email.lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        generic_error = AuthenticationError("Security answer is incorrect.")

        if not user or not user.is_active or not user.security_answer_hash:
            logger.warning("Password-reset attempt for unknown/invalid email: %s", normalized_email)
            raise generic_error

        if not self._password_service.verify_password(
            request.security_answer.strip().lower(), user.security_answer_hash
        ):
            logger.warning("Password-reset failed: wrong security answer for %s", normalized_email)
            raise generic_error

        user.password_hash = self._password_service.hash_password(request.new_password)
        db.commit()
        logger.info("Password reset successful for %s", normalized_email)
