"""
Application-wide logging configuration.

Sets up a root logger with both a rotating file handler (logs/app.log) and a
console handler, at INFO level by default. Call `setup_logging()` once, on
application startup, before any other module logs anything.

Also sets up a dedicated `medical_ai` logger (logs/medical_ai.log) used
specifically by Module 2.5's medical-intelligence services (symptom
detection, disease predictions, severity results, emergency alerts, RAG
context-injection decisions) so those events can be audited independently
of general application logs.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings
from app.core.constants import (
    AUTH_LOG_FILENAME,
    HISTORY_LOG_FILENAME,
    MEDICAL_AI_LOG_FILENAME,
    OCR_LOG_FILENAME,
    REPORT_ANALYSIS_LOG_FILENAME,
    SYSTEM_LOG_FILENAME,
)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

MEDICAL_AI_LOGGER_NAME = "medical_ai"
REPORT_ANALYSIS_LOGGER_NAME = "report_analysis"
AUTH_LOGGER_NAME = "auth"
HISTORY_LOGGER_NAME = "history"
OCR_LOGGER_NAME = "ocr"
SYSTEM_LOGGER_NAME = "system"


def get_medical_ai_logger() -> logging.Logger:
    """Return the dedicated logger for Module 2.5 medical-intelligence events."""
    return logging.getLogger(MEDICAL_AI_LOGGER_NAME)


def get_report_analysis_logger() -> logging.Logger:
    """Return the dedicated logger for Module 3 report-analysis events."""
    return logging.getLogger(REPORT_ANALYSIS_LOGGER_NAME)


def get_auth_logger() -> logging.Logger:
    """Return the dedicated logger for Module 4 auth events (registrations, logins)."""
    return logging.getLogger(AUTH_LOGGER_NAME)


def get_history_logger() -> logging.Logger:
    """Return the dedicated logger for Module 5 history/dashboard events."""
    return logging.getLogger(HISTORY_LOGGER_NAME)


def _setup_named_file_logger(name: str, log_file_path: str, formatter: logging.Formatter,
                              console_handler: logging.Handler) -> None:
    """Configure a named logger with its own rotating file handler, isolated
    from the root logger (propagate=False) so each module's audit log stays
    independently readable, while still surfacing to the console."""
    file_handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    named_logger = logging.getLogger(name)
    named_logger.setLevel(logging.INFO)
    named_logger.handlers = []
    named_logger.addHandler(file_handler)
    named_logger.addHandler(console_handler)
    named_logger.propagate = False


def setup_logging() -> None:
    settings = get_settings()
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    log_file_path = os.path.join(settings.LOG_DIR, "app.log")
    medical_ai_log_path = os.path.join(settings.LOG_DIR, MEDICAL_AI_LOG_FILENAME)
    report_analysis_log_path = os.path.join(settings.LOG_DIR, REPORT_ANALYSIS_LOG_FILENAME)
    auth_log_path = os.path.join(settings.LOG_DIR, AUTH_LOG_FILENAME)
    history_log_path = os.path.join(settings.LOG_DIR, HISTORY_LOG_FILENAME)
    ocr_log_path = os.path.join(settings.LOG_DIR, OCR_LOG_FILENAME)
    system_log_path = os.path.join(settings.LOG_DIR, SYSTEM_LOG_FILENAME)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Avoid duplicate handlers if setup_logging() is ever called more than once
    # (e.g. under pytest or reload).
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Quiet down noisy third-party libraries; we still want WARNING/ERROR from them.
    for noisy_logger in ("chromadb", "sentence_transformers", "httpx", "httpcore", "urllib3", "pdfminer"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Dedicated audit logs for Modules 2.5, 3, 4, and 5, each independent of
    # app.log and of each other.
    _setup_named_file_logger(MEDICAL_AI_LOGGER_NAME, medical_ai_log_path, formatter, console_handler)
    _setup_named_file_logger(REPORT_ANALYSIS_LOGGER_NAME, report_analysis_log_path, formatter, console_handler)
    _setup_named_file_logger(AUTH_LOGGER_NAME, auth_log_path, formatter, console_handler)
    _setup_named_file_logger(HISTORY_LOGGER_NAME, history_log_path, formatter, console_handler)
    _setup_named_file_logger(OCR_LOGGER_NAME, ocr_log_path, formatter, console_handler)
    _setup_named_file_logger(SYSTEM_LOGGER_NAME, system_log_path, formatter, console_handler)

    logging.getLogger(__name__).info("Logging initialized. Writing to %s", log_file_path)
    logging.getLogger(__name__).info("Medical AI audit log writing to %s", medical_ai_log_path)
    logging.getLogger(__name__).info("Report analysis audit log writing to %s", report_analysis_log_path)
    logging.getLogger(__name__).info("Auth audit log writing to %s", auth_log_path)
    logging.getLogger(__name__).info("History audit log writing to %s", history_log_path)
