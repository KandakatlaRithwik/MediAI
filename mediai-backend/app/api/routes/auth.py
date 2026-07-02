"""
Authentication endpoints (Module 4).

All four endpoints require a database connection; if Postgres is
unreachable, `Depends(get_db)` raises DatabaseUnavailableError, which the
global exception handler turns into a clean 503 - consistent with every
other error path in this app.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_auth_service
from app.database.connection import get_db
from app.database.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    SECURITY_QUESTIONS,
    SecurityQuestionListResponse,
    SecurityQuestionLookupRequest,
    SecurityQuestionLookupResponse,
    TokenResponse,
    UserProfileResponse,
)
from app.services.auth_service import AuthService
from app.services.role_service import get_current_user

logger = logging.getLogger("auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Register a new user",
    description="Create a new Patient, Doctor, or Admin account. Passwords are hashed with bcrypt and never stored in plaintext.",
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    service.register(db, request)
    return RegisterResponse(message="User created successfully")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive an access/refresh token pair",
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return service.login(db, request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a valid refresh token for a new access/refresh token pair",
)
async def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return service.refresh(db, request.refresh_token)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get the current authenticated user's profile",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)


@router.get(
    "/security-questions",
    response_model=SecurityQuestionListResponse,
    summary="List the predefined security questions offered at registration",
)
async def list_security_questions() -> SecurityQuestionListResponse:
    return SecurityQuestionListResponse(questions=list(SECURITY_QUESTIONS))


@router.post(
    "/security-question",
    response_model=SecurityQuestionLookupResponse,
    summary="Look up the security question configured for a given account (Forgot Password step 1)",
)
async def lookup_security_question(
    request: SecurityQuestionLookupRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> SecurityQuestionLookupResponse:
    question = service.get_security_question(db, request.email)
    return SecurityQuestionLookupResponse(security_question=question)


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
    summary="Reset a password by verifying the account's security answer (Forgot Password step 2)",
)
async def reset_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> PasswordResetResponse:
    service.reset_password(db, request)
    return PasswordResetResponse()
