"""
Centralized application configuration.

All environment-driven settings live here, loaded via pydantic-settings from
a `.env` file (see `.env.example`). Access settings anywhere in the app via
`get_settings()`, which is cached so the `.env` file and embedding model
config are only resolved once per process.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    APP_NAME: str = "AI-Powered Medical Assistant - Medical RAG Engine"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.5.0"

    # --- Gemini LLM ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"

    # --- Embeddings ---
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # --- Storage paths ---
    CHROMA_DB_PATH: str = "./chroma_db"
    UPLOAD_DIR: str = "./uploads"
    LOG_DIR: str = "./logs"

    # --- Chunking ---
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # --- Retrieval ---
    RETRIEVAL_TOP_K: int = 5

    # --- Upload security ---
    MAX_FILE_SIZE_MB: int = 10
    # Extension allow-list used by /analyze-report. Images (.jpg/.jpeg/.png)
    # are also accepted here and routed automatically into the OCR pipeline
    # by the frontend via the /analyze-image-report endpoint.
    ALLOWED_EXTENSIONS: str = ".pdf,.txt,.docx,.jpg,.jpeg,.png"

    # --- Database (future-ready; not required for Module 1 to function) ---
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/medical_assistant"

    # --- Auth / JWT (Module 4) ---
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- OCR (Module 6) ---
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "en"

    # --- DB Connection Pool (Module 7) ---
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # --- CORS ---
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton for the process lifetime)."""
    return Settings()
