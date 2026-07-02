"""
Embedding generation service.

Wraps a sentence-transformers model (default: all-MiniLM-L6-v2) as a
singleton so the (relatively expensive) model load happens exactly once per
process, regardless of how many requests or chunks need embeddings.
"""

import logging
import threading
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        settings = get_settings()
        logger.info("Loading embedding model '%s' (one-time load)...", settings.EMBEDDING_MODEL_NAME)
        try:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception as exc:
            logger.error("Failed to load embedding model: %s", exc)
            raise EmbeddingGenerationError(f"Failed to load embedding model: {exc}") from exc
        logger.info("Embedding model loaded successfully.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of chunk texts (document-side)."""
        if not texts:
            return []
        try:
            vectors = self._model.encode(
                texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True
            )
            return vectors.tolist()
        except Exception as exc:
            logger.error("Embedding generation failed for %d text(s): %s", len(texts), exc)
            raise EmbeddingGenerationError(f"Failed to generate embeddings: {exc}") from exc

    def embed_query(self, text: str) -> List[float]:
        """Generate a single embedding for a user query."""
        try:
            vector = self._model.encode(
                [text], show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True
            )[0]
            return vector.tolist()
        except Exception as exc:
            logger.error("Embedding generation failed for query: %s", exc)
            raise EmbeddingGenerationError(f"Failed to generate query embedding: {exc}") from exc
