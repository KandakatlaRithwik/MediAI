"""
Patient history models (Module 5 - Patient Medical History & Record Management).

Three tables, one per history type, each FK'd to `users.id`:
  - PatientHistory: symptom-checker results (Module 2.5)
  - MedicalReportHistory: report-analyzer results (Module 3)
  - ChatHistory: /ask question/answer pairs (Module 1)

`symptoms`, `predicted_diseases`, and `risk_assessment` are stored as JSON
columns rather than normalized into their own tables - these are
denormalized snapshots of what the patient was told at the time, not data
that needs independent querying/joining, so JSON keeps the schema simple
without losing any information.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class PatientHistory(Base):
    __tablename__ = "patient_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symptoms = Column(JSON, nullable=False, default=list)
    predicted_diseases = Column(JSON, nullable=False, default=list)
    severity = Column(String(20), nullable=False)
    emergency_status = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    patient = relationship("User", back_populates="symptom_history")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PatientHistory id={self.id} patient_id={self.patient_id} severity={self.severity}>"


class MedicalReportHistory(Base):
    __tablename__ = "medical_report_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(100), nullable=False)
    report_summary = Column(Text, nullable=False)
    risk_assessment = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    patient = relationship("User", back_populates="report_history")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MedicalReportHistory id={self.id} patient_id={self.patient_id} type={self.report_type!r}>"


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    patient = relationship("User", back_populates="chat_history")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChatHistory id={self.id} patient_id={self.patient_id}>"
