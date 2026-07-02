"""
Text chunking utilities.

Splits loaded documents into overlapping chunks sized appropriately for both
embedding quality and LLM context limits, using LangChain's
RecursiveCharacterTextSplitter. Chunk size/overlap are configurable via
settings (CHUNK_SIZE / CHUNK_OVERLAP) rather than hardcoded.
"""

import logging
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument

logger = logging.getLogger(__name__)


def chunk_documents(
    documents: List[LCDocument],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[LCDocument]:
    """Split a list of documents into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info(
        "Chunked %d document(s) into %d chunk(s) (size=%d, overlap=%d)",
        len(documents), len(chunks), chunk_size, chunk_overlap,
    )
    return chunks
