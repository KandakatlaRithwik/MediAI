"""Request/response schemas for authentication (Module 4)."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.database.models.user import UserRole

# Predefined security questions offered to users at registration and reused
# in the Forgot-Password recovery flow. Keeping them server-side enforces a
# closed vocabulary (safer to hash/compare and defend against typos).
SECURITY_QUESTIONS: List[str] = [
    "What was the name of your first school?",
    "What is your childhood nickname?",
    "Who was your favorite teacher?",
    "What is your favorite color?",
    "What was the name of your first pet?",
    "In what city were you born?",
]


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Minimum 8 characters.")
    phone: Optional[str] = Field(default=None, max_length=30)
    role: UserRole = Field(default=UserRole.PATIENT)
    security_question: str = Field(..., min_length=3, max_length=255,
        description="One of the predefined security questions returned from GET /auth/security-questions.")
    security_answer: str = Field(..., min_length=1, max_length=255,
        description="User's answer to the chosen security question. Stored bcrypt-hashed, never in plaintext.")

    @field_validator("password")
    @classmethod
    def _validate_password_strength(cls, value: str) -> str:
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter.")
        return value

    @field_validator("security_question")
    @classmethod
    def _validate_security_question(cls, value: str) -> str:
        if value not in SECURITY_QUESTIONS:
            raise ValueError("Security question must be one of the predefined options.")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "password": "password123",
                "role": "PATIENT",
                "security_question": "What was the name of your first pet?",
                "security_answer": "Buddy",
            }
        }
    }


class RegisterResponse(BaseModel):
    message: str = "User created successfully"

    model_config = {"json_schema_extra": {"example": {"message": "User created successfully"}}}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    model_config = {
        "json_schema_extra": {"example": {"email": "john@example.com", "password": "password123"}}
    }


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = {"json_schema_extra": {"example": {"refresh_token": "<refresh token>"}}}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "<jwt access token>",
                "refresh_token": "<jwt refresh token>",
                "token_type": "bearer",
            }
        }
    }


class UserProfileResponse(BaseModel):
    uuid: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": None,
                "role": "PATIENT",
                "is_active": True,
                "created_at": "2026-06-20T10:00:00Z",
            }
        },
    }


class SecurityQuestionListResponse(BaseModel):
    questions: List[str]


class SecurityQuestionLookupRequest(BaseModel):
    email: EmailStr


class SecurityQuestionLookupResponse(BaseModel):
    security_question: str


class PasswordResetRequest(BaseModel):
    email: EmailStr
    security_answer: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _validate_password_strength(cls, value: str) -> str:
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isalpha() for c in value):
            raise ValueError("Password must contain at least one letter.")
        return value


class PasswordResetResponse(BaseModel):
    message: str = "Password reset successfully. Please sign in with your new password."
