"""
RAG query endpoint - ask medical questions against ingested documents.

Module 5: if the caller is authenticated, their recent history is loaded
and injected into Gemini's context (see RAGService.answer_question), and
the question/answer pair is automatically saved to their chat history.
Both are fully optional and best-effort - an anonymous call, or a
history-save failure, never affects the response returned to the caller.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends

from app.api.deps import get_history_service, get_rag_service
from app.database.connection import get_db_session_or_none
from app.database.models.user import User
from app.schemas.query import QueryRequest
from app.schemas.response import AskResponse
from app.services.history_service import HistoryService
from app.services.rag_service import RAGService
from app.services.role_service import get_optional_current_user

logger = logging.getLogger("history")

router = APIRouter(tags=["RAG Query"])


def _save_chat_history_best_effort(
    history_service: HistoryService, current_user: Optional[User], question: str, answer: str
) -> None:
    if current_user is None:
        return
    db = get_db_session_or_none()
    if db is None:
        return
    try:
        history_service.save_chat_history(db, patient_id=current_user.id, question=question, response=answer)
    except Exception as exc:  # noqa: BLE001 - history saving must never break the endpoint
        logger.error("Failed to save chat history for user_id=%s: %s", current_user.id, exc)
    finally:
        db.close()


@router.post("/ask", response_model=AskResponse, summary="Ask a medical question")
async def ask_question(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
    history_service: HistoryService = Depends(get_history_service),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> AskResponse:
    """
    Retrieve relevant context from ingested medical documents and generate a
    grounded answer via Gemini. If called with a valid Bearer token, the
    caller's recent history (symptoms, reports, prior questions) is loaded
    into context, and this question/answer pair is saved to their chat
    history. Domain errors (embedding/vector store/LLM failures) are
    handled globally by the registered exception handlers.
    """
    logger.info("Received question: %s", request.question)
    response = rag_service.answer_question(
        question=request.question,
        top_k=request.top_k,
        source_filter=request.source_filter,
        current_user=current_user,
    )
    _save_chat_history_best_effort(history_service, current_user, request.question, response.answer)
    return response
