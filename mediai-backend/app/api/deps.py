"""
FastAPI dependency providers.

Centralizing dependency construction here keeps routes free of
instantiation logic and makes it trivial to override services in tests via
`app.dependency_overrides[get_rag_service] = lambda: fake_service`.
"""

from functools import lru_cache

from app.services.auth_service import AuthService
from app.services.history_service import HistoryService
from app.services.medical_record_service import MedicalRecordService
from app.services.patient_service import PatientService
from app.services.rag_service import RAGService
from app.services.report_analysis_service import ReportAnalysisService
from app.services.report_image_parser_service import ReportImageParserService
from app.services.symptom_checker_service import SymptomCheckerService
from app.services.system_health_service import SystemHealthService


@lru_cache()
def _rag_service_singleton() -> RAGService:
    # RAGService internally uses singletons for the embedding model, vector
    # store, and LLM client, so this just avoids re-running __init__ logic
    # (cheap, but unnecessary) on every request.
    return RAGService()


def get_rag_service() -> RAGService:
    return _rag_service_singleton()


@lru_cache()
def _symptom_checker_service_singleton() -> SymptomCheckerService:
    return SymptomCheckerService()


def get_symptom_checker_service() -> SymptomCheckerService:
    return _symptom_checker_service_singleton()


@lru_cache()
def _report_analysis_service_singleton() -> ReportAnalysisService:
    return ReportAnalysisService()


def get_report_analysis_service() -> ReportAnalysisService:
    return _report_analysis_service_singleton()


@lru_cache()
def _auth_service_singleton() -> AuthService:
    return AuthService()


def get_auth_service() -> AuthService:
    return _auth_service_singleton()


@lru_cache()
def _history_service_singleton() -> HistoryService:
    return HistoryService()


def get_history_service() -> HistoryService:
    return _history_service_singleton()


@lru_cache()
def _patient_service_singleton() -> PatientService:
    return PatientService()


def get_patient_service() -> PatientService:
    return _patient_service_singleton()


@lru_cache()
def _medical_record_service_singleton() -> MedicalRecordService:
    return MedicalRecordService()


def get_medical_record_service() -> MedicalRecordService:
    return _medical_record_service_singleton()


@lru_cache()
def _report_image_parser_singleton() -> ReportImageParserService:
    return ReportImageParserService()


def get_report_image_parser_service() -> ReportImageParserService:
    return _report_image_parser_singleton()


@lru_cache()
def _system_health_service_singleton() -> SystemHealthService:
    return SystemHealthService()


def get_system_health_service() -> SystemHealthService:
    return _system_health_service_singleton()
