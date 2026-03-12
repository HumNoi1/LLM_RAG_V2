"""
RAG Service — LlamaIndex VectorStoreIndex + Groq QueryEngine.
BE-S responsibility (Sprint 2).

Pipeline per question:
  1. Build retriever filtered by exam_id + doc_type in [answer_key, rubric, course_material]
  2. Retrieve top-k relevant chunks
  3. Format grading prompt with question, rubric chunks, student answer
  4. Call Groq llama-3.3-70b-versatile
  5. Parse JSON response → score + reasoning
"""
import asyncio
import json
import logging
import re
from uuid import UUID

from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.llms.groq import Groq

from app.config import get_settings
from app.core.exceptions import LLMException
from app.services.embedding_service import get_embed_model, get_index_for_exam

logger = logging.getLogger(__name__)

# ── Rate limiting config ──────────────────────────────────────────────────────

_GROQ_MAX_RETRIES = 3
_GROQ_BASE_DELAY = 2  # seconds

# ── Grading prompt template ───────────────────────────────────────────────────

GRADING_PROMPT = """\
คุณเป็นผู้เชี่ยวชาญตรวจข้อสอบที่แม่นยำและยุติธรรม ให้ตรวจคำตอบนักเรียนตาม rubric และเฉลยที่ให้มา

โจทย์: {question}
คะแนนเต็ม: {max_score}

คำตอบนักเรียน:
{student_answer}

Context (เฉลย + Rubric + เนื้อหาวิชา):
{context}

ให้ตรวจคำตอบตามเกณฑ์และตอบกลับเป็น JSON เท่านั้น (ไม่ต้องมีข้อความอื่น):
{{
  "score": <คะแนนที่ได้ เป็นตัวเลขทศนิยม>,
  "reasoning": "<เหตุผลการให้คะแนน อธิบายว่าตอบถูกหรือผิดและขาดอะไร>",
  "covered_points": ["<ประเด็นที่ตอบถูก>"],
  "missed_points": ["<ประเด็นที่ขาดหรือตอบผิด>"]
}}"""


def _get_groq_llm() -> Groq:
    """Create a Groq LLM instance from settings."""
    settings = get_settings()
    return Groq(
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )


def _parse_json_from_response(text: str) -> dict:
    """Extract JSON object from LLM response text."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Fallback: extract first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No valid JSON found in LLM response")


async def _call_llm_with_retry(llm: Groq, messages: list[ChatMessage]) -> str:
    """Call Groq LLM with exponential backoff on HTTP 429 rate limit errors.

    Retries up to _GROQ_MAX_RETRIES times with exponential backoff starting at
    _GROQ_BASE_DELAY seconds.
    """
    delay = _GROQ_BASE_DELAY
    for attempt in range(_GROQ_MAX_RETRIES):
        try:
            response = await asyncio.to_thread(llm.chat, messages)
            return response.message.content
        except Exception as e:
            is_rate_limit = "429" in str(e) or "rate limit" in str(e).lower()
            if is_rate_limit and attempt < _GROQ_MAX_RETRIES - 1:
                logger.warning(
                    "Groq rate limit hit, retrying in %ds (attempt %d/%d)",
                    delay, attempt + 1, _GROQ_MAX_RETRIES,
                )
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise


async def retrieve_context(
    exam_id: UUID,
    question_text: str,
    top_k: int = 5,
) -> str:
    """Retrieve relevant chunks from Qdrant filtered by exam_id.

    Returns concatenated context text.
    """
    Settings.embed_model = get_embed_model()

    index = get_index_for_exam(exam_id)

    # Build retriever with metadata filter for this exam
    retriever = index.as_retriever(
        similarity_top_k=top_k,
        filters=MetadataFilters(
            filters=[MetadataFilter(key="exam_id", value=str(exam_id))]
        ),
    )

    nodes = await retriever.aretrieve(question_text)

    if not nodes:
        logger.warning("No context chunks found for exam_id=%s, query='%s'", exam_id, question_text[:50])
        return "(ไม่พบเนื้อหาอ้างอิง)"

    # Concatenate chunk texts with metadata hints
    context_parts = []
    for i, node in enumerate(nodes, 1):
        doc_type = node.metadata.get("doc_type", "unknown")
        context_parts.append(f"[{doc_type} chunk {i}]\n{node.text}")

    return "\n\n---\n\n".join(context_parts)


async def query_for_grading(
    exam_id: UUID,
    question_text: str,
    student_answer: str,
    max_score: float,
) -> dict:
    """Retrieve relevant context and call LLM to grade a single answer.

    Args:
        exam_id:        Exam UUID — used to filter Qdrant by metadata.
        question_text:  The exam question text.
        student_answer: The student's answer for this question.
        max_score:      Maximum score for this question.

    Returns:
        dict with keys: score (float), reasoning (str), covered_points (list), missed_points (list)
    """
    try:
        # 1. Retrieve context from RAG
        context = await retrieve_context(exam_id, question_text)

        # 2. Build grading prompt
        prompt = GRADING_PROMPT.format(
            question=question_text,
            max_score=max_score,
            student_answer=student_answer,
            context=context,
        )

        # 3. Call Groq LLM with retry on rate limit
        llm = _get_groq_llm()
        raw_response = await _call_llm_with_retry(llm, [ChatMessage(role="user", content=prompt)])

        logger.debug("LLM response for exam=%s: %s", exam_id, raw_response[:200])

        # 4. Parse JSON response
        result = _parse_json_from_response(raw_response)

        # Validate and clamp score
        score = float(result.get("score", 0))
        score = max(0.0, min(score, max_score))

        return {
            "score": score,
            "reasoning": result.get("reasoning", ""),
            "covered_points": result.get("covered_points", []),
            "missed_points": result.get("missed_points", []),
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse LLM grading response: %s", e)
        raise LLMException(f"Failed to parse grading response: {e}") from e
    except LLMException:
        raise
    except Exception as e:
        logger.error("RAG grading query failed for exam=%s: %s", exam_id, e)
        raise LLMException(str(e)) from e
