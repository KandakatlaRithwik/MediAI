"""
Retrieval service.

Given a user question, embeds it and runs a top-K similarity search against
the vector store, returning ranked chunks with relevance scores and the
distinct set of source documents. Supports optional metadata filtering by
source filename.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.core.config import get_settings
from app.rag.vector_store import VectorStoreService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    source: str
    relevance_score: float
    chunk_index: Optional[int] = None


class RetrievalService:
    def __init__(self) -> None:
        self._embedding_service = EmbeddingService()
        self._vector_store = VectorStoreService()
        self._settings = get_settings()

    def retrieve(
        self,
        question: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None,
    ) -> Tuple[List[RetrievedChunk], List[str]]:
        """Retrieve the most relevant chunks for a question.

        Returns a tuple of (ranked chunks, sorted unique source filenames).
        """
        effective_top_k = top_k or self._settings.RETRIEVAL_TOP_K
        query_embedding = self._embedding_service.embed_query(question)

        where = {"source": source_filter} if source_filter else None
        results = self._vector_store.search(query_embedding, top_k=effective_top_k, where=where)

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        chunks: List[RetrievedChunk] = []
        sources: set = set()

        for text, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            source = metadata.get("source", "unknown")
            # Cosine distance -> a simple, bounded similarity score for display/ranking.
            relevance_score = max(0.0, 1.0 - float(distance))
            chunks.append(
                RetrievedChunk(
                    text=text,
                    source=source,
                    relevance_score=round(relevance_score, 4),
                    chunk_index=metadata.get("chunk_index"),
                )
            )
            sources.add(source)

        logger.info(
            "Retrieved %d chunk(s) from %d source(s) for question (top_k=%d)",
            len(chunks), len(sources), effective_top_k,
        )
        return chunks, sorted(sources)
