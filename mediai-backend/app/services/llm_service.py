"""
LLM service - Gemini integration (singleton).

Builds a careful, grounding-only prompt from CONTEXT and QUESTION, applies the
medical safety system prompt, and produces a structured Markdown response.
"""

import logging
import threading
from typing import List, Optional

from google import genai
from google.genai import types as genai_types

from app.core.config import get_settings
from app.core.constants import MEDICAL_SYSTEM_PROMPT
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


def _build_user_prompt(question: str, context_chunks: List[str]) -> str:
    if context_chunks:
        labeled = []
        for i, chunk in enumerate(context_chunks, start=1):
            labeled.append(f"[CHUNK {i}]\n{chunk}")
        context_block = "\n\n---\n\n".join(labeled)
    else:
        context_block = "(no context retrieved)"

    return (
        "CONTEXT (retrieved knowledge, symptom analysis, report analysis, and patient history):\n"
        f"{context_block}\n\n"
        "USER QUESTION:\n"
        f"{question}\n\n"
        "Respond using ONLY the CONTEXT above, strictly following every SAFETY RULE and the "
        "exact OUTPUT FORMAT defined in the system instructions. Use Markdown headings."
    )


class LLMService:
    _instance: Optional["LLMService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LLMService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            logger.warning(
                "GEMINI_API_KEY is not set. /ask will fail until it is configured in .env"
            )
        self._model_name = settings.GEMINI_MODEL_NAME
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        user_prompt = _build_user_prompt(question, context_chunks)

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=user_prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=MEDICAL_SYSTEM_PROMPT,
                    temperature=0.15,
                    top_p=0.9,
                    max_output_tokens=2048,
                ),
            )
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise LLMServiceError(f"The AI model failed to generate a response: {exc}") from exc

        answer_text = (getattr(response, "text", None) or "").strip()
        if not answer_text:
            logger.warning("Gemini returned an empty response for question: %s", question)
            raise LLMServiceError("The AI model returned an empty response. Please try again.")

        return answer_text
