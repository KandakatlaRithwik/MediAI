"""
ChromaDB-backed vector store service.

Wraps a persistent ChromaDB collection and exposes a small, storage-agnostic
interface (add / search / count) so the rest of the application never talks
to ChromaDB directly. Implemented as a singleton: the client and collection
are initialized once and reused across requests.
"""

import logging
import os
import threading
from typing import Dict, List, Optional

import chromadb

from app.core.config import get_settings
from app.core.constants import CHROMA_COLLECTION_NAME
from app.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class VectorStoreService:
    _instance: Optional["VectorStoreService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "VectorStoreService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        settings = get_settings()
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)

        logger.info("Initializing ChromaDB persistent client at '%s'", settings.CHROMA_DB_PATH)
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=chromadb.config.Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
    ) -> None:
        """Persist a batch of chunk embeddings with their text and metadata."""
        if not ids:
            return
        try:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
        except Exception as exc:
            logger.error("Failed to add %d chunk(s) to vector store: %s", len(ids), exc)
            raise VectorStoreError(f"Failed to store document vectors: {exc}") from exc

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict] = None,
    ) -> Dict:
        """Run a similarity search and return the raw ChromaDB result dict."""
        try:
            return self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
            )
        except Exception as exc:
            logger.error("Vector similarity search failed: %s", exc)
            raise VectorStoreError(f"Failed to search document vectors: {exc}") from exc

    def count(self) -> int:
        """Return the total number of chunks currently stored."""
        try:
            return self._collection.count()
        except Exception as exc:
            logger.error("Failed to count vector store entries: %s", exc)
            raise VectorStoreError(f"Failed to read vector store state: {exc}") from exc
