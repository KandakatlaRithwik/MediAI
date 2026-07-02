"""
User model and role enum (Module 4 - Authentication & Role Management).

`id` is the internal auto-incrementing primary key (used for foreign keys
and joins); `uuid` is a separate, publicly-exposable unique identifier so
internal sequential IDs are never leaked via the API (e.g. in JWT subject
claims or response bodies) - a small but deliberate security hardening.
"""

import enum
import uuid as uuid_lib

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class UserRole(str, enum.Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.PATIENT)
    is_active = Column(Boolean, nullable=False, default=True)
    security_question = Column(String(255), nullable=True)
    security_answer_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    symptom_history = relationship("PatientHistory", back_populates="patient", cascade="all, delete-orphan")
    report_history = relationship("MedicalReportHistory", back_populates="patient", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
