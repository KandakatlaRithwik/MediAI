"""
Document ingestion pipeline.

Orchestrates the full Module 1 ingestion flow:

    file path -> load -> chunk -> embed -> store in ChromaDB

This is intentionally the *only* place that wires document_loader,
chunking, EmbeddingService, and VectorStoreService together, so the upload
route and RAGService stay thin and the flow is easy to test/extend.
"""

import logging
from typing import List
from uuid import uuid4

from app.core.config import get_settings
from app.core.exceptions import DocumentProcessingError
from app.rag.chunking import chunk_documents
from app.rag.document_loader import load_document
from app.rag.vector_store import VectorStoreService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self) -> None:
        self._embedding_service = EmbeddingService()
        self._vector_store = VectorStoreService()
        self._settings = get_settings()

    def ingest(self, file_path: str, filename: str) -> int:
        """Run the full ingestion pipeline for a single uploaded file.

        Returns the number of chunks stored in the vector database.
        """
        documents = load_document(file_path)

        chunks = chunk_documents(
            documents,
            chunk_size=self._settings.CHUNK_SIZE,
            chunk_overlap=self._settings.CHUNK_OVERLAP,
        )
        if not chunks:
            raise DocumentProcessingError(f"No content could be extracted from '{filename}'.")

        texts: List[str] = [chunk.page_content for chunk in chunks]
        embeddings = self._embedding_service.embed_documents(texts)

        ids = [f"{filename}__{uuid4().hex}__{i}" for i in range(len(texts))]
        metadatas = [
            {
                "source": filename,
                "chunk_index": i,
                "page": chunk.metadata.get("page", None) if isinstance(chunk.metadata, dict) else None,
            }
            for i, chunk in enumerate(chunks)
        ]

        self._vector_store.add_chunks(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)

        logger.info("Ingested '%s' -> %d chunk(s) stored in vector database.", filename, len(texts))
        return len(texts)
