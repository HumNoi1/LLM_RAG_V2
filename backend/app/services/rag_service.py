"""
RAG Service — LlamaIndex VectorStoreIndex + Groq QueryEngine.
BE-S responsibility (Sprint 2).
Sprint 4: Performance tuning — configurable top_k, score_threshold, retry params.
          Prompt optimization — improved grading prompt with detailed rubric instructions.

Pipeline per question:
  1. Build retriever filtered by exam_id + doc_type in [answer_key, rubric, course_material]
  2. Retrieve top-k relevant chunks (configurable via QDRANT_TOP_K)
  3. Filter low-quality chunks by score_threshold (configurable via QDRANT_SCORE_THRESHOLD)
  4. Format grading prompt with question, rubric chunks, student answer
  5. Call Groq llama-3.3-70b-versatile with configurable retry/timeout
  6. Parse JSON response → score + reasoning
"""

import asyncio
import json
import logging
import re
from uuid import UUID

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.llms import ChatMessage
from llama_index.core.vector_stores import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.llms.groq import Groq

from app.config import get_settings
from app.core.exceptions import LLMException
from app.services.embedding_service import get_embed_model, _get_async_vector_store

logger = logging.getLogger(__name__)

# ── Grading prompt template (Sprint 4: Optimized) ────────────────────────────
# ปรับ prompt ให้ละเอียดขึ้น เพิ่มเกณฑ์การให้คะแนนที่ชัดเจน
# และลด hallucination โดยเน้นให้ LLM อ้างอิงจาก context เท่านั้น

GRADING_PROMPT = """\
คุณเป็นผู้เชี่ยวชาญตรวจข้อสอบอัตนัยที่มีความแม่นยำและยุติธรรม

## กฎการตรวจ
1. ให้คะแนนโดยอ้างอิงจาก Context (เฉลย + Rubric + เนื้อหาวิชา) ที่ให้มาเท่านั้น
2. หากคำตอบถูกต้องแต่ใช้คำต่างจากเฉลย ให้ได้คะแนนเต็มในประเด็นนั้น
3. หากคำตอบถูกบางส่วน ให้คะแนนตามสัดส่วนของความถูกต้อง
4. หากคำตอบไม่เกี่ยวข้องกับคำถามเลย ให้ 0 คะแนน
5. คะแนนต้องอยู่ระหว่าง 0 ถึง {max_score} เท่านั้น
6. ให้เหตุผลประกอบการให้คะแนนเป็นภาษาไทย

## โจทย์
{question}

## คะแนนเต็ม
{max_score}

## คำตอบนักเรียน
{student_answer}

## Context (เฉลย + Rubric + เนื้อหาวิชา)
{context}

## คำสั่ง
ตรวจคำตอบนักเรียนเทียบกับ Context ข้างต้น แล้วตอบกลับเป็น JSON เท่านั้น (ห้ามมีข้อความอื่นนอกจาก JSON):
{{
  "score": <คะแนนที่ได้ เป็นตัวเลขทศนิยม 1 ตำแหน่ง>,
  "reasoning": "<เหตุผลการให้คะแนน อธิบายสั้นๆ ว่าตอบถูกหรือผิดอย่างไร>",
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
        request_timeout=settings.llm_request_timeout,
    )


def _parse_json_from_response(text: str) -> dict:
    """Extract JSON object from LLM response text.

    Sprint 4: เพิ่ม fallback หลายขั้นตอนสำหรับ parse JSON ที่ LLM อาจตอบมาไม่สมบูรณ์
    """
    # ลองเอา markdown code block ออกก่อน (LLM อาจห่อด้วย ```json ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # ลอง parse ตรงๆ ก่อน
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # Fallback: extract first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in LLM response: {text[:200]}")


async def _call_llm_with_retry(llm: Groq, messages: list[ChatMessage]) -> str:
    """Call Groq LLM with exponential backoff on rate limit and timeout errors.

    Sprint 4: ใช้ค่า retry จาก config แทน hardcode
    รองรับทั้ง rate limit (429) และ timeout errors
    """
    settings = get_settings()
    max_retries = settings.llm_max_retries
    delay = settings.llm_retry_base_delay

    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(llm.chat, messages)
            if response.message.content is None:
                raise ValueError("Empty response content from LLM")
            return str(response.message.content)

        except Exception as e:
            error_str = str(e).lower()
            is_retryable = (
                "429" in str(e)
                or "rate limit" in error_str
                or "timeout" in error_str
                or "timed out" in error_str
                or "connection" in error_str
                or "503" in str(e)
                or "service unavailable" in error_str
            )

            if is_retryable and attempt < max_retries - 1:
                logger.warning(
                    "Groq API error (retryable), retrying in %ds (attempt %d/%d): %s",
                    delay,
                    attempt + 1,
                    max_retries,
                    str(e)[:100],
                )
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logger.error(
                    "Groq API call failed after %d attempts: %s",
                    attempt + 1,
                    str(e)[:200],
                )
                raise

    raise RuntimeError("Failed to get LLM response after retries")


async def retrieve_context(
    exam_id: UUID,
    question_text: str,
    top_k: int | None = None,
) -> str:
    """Retrieve relevant chunks from Qdrant filtered by exam_id.

    Sprint 4: ใช้ configurable top_k และ score_threshold จาก Settings
    เพื่อให้ปรับคุณภาพการ retrieve ได้ตาม use case

    Returns concatenated context text.
    """
    settings = get_settings()
    if top_k is None:
        top_k = settings.qdrant_top_k

    Settings.embed_model = get_embed_model()

    # Use async vector store for async retrieval
    vector_store = await _get_async_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # Build retriever with metadata filter for this exam and allowed document types
    retriever = index.as_retriever(
        similarity_top_k=top_k,
        filters=MetadataFilters(
            filters=[
                MetadataFilter(key="exam_id", value=str(exam_id)),
                MetadataFilter(
                    key="doc_type",
                    value=["answer_key", "rubric", "course_material"],
                    operator=FilterOperator.IN,
                ),
            ]
        ),
    )

    nodes = await retriever.aretrieve(question_text)

    if not nodes:
        logger.warning(
            "No context chunks found for exam_id=%s, query='%s'",
            exam_id,
            question_text[:50],
        )
        return "(ไม่พบเนื้อหาอ้างอิง)"

    # Sprint 4: กรอง chunks ที่มี score ต่ำกว่า threshold ออก
    score_threshold = settings.qdrant_score_threshold
    filtered_nodes = [
        node for node in nodes if node.score is None or node.score >= score_threshold
    ]

    if not filtered_nodes:
        logger.warning(
            "All chunks below score_threshold=%.2f for exam_id=%s, using top result anyway",
            score_threshold,
            exam_id,
        )
        filtered_nodes = nodes[:1]  # ใช้ผลลัพธ์อันดับ 1 ไว้ก่อนเพื่อไม่ให้ grade ล้มเหลว

    # Concatenate chunk texts with metadata hints
    context_parts = []
    for i, node in enumerate(filtered_nodes, 1):
        doc_type = node.metadata.get("doc_type", "unknown")
        score_info = f" (score: {node.score:.3f})" if node.score is not None else ""
        context_parts.append(f"[{doc_type} chunk {i}{score_info}]\n{node.text}")

    logger.info(
        "Retrieved %d/%d chunks for exam_id=%s (top_k=%d, threshold=%.2f)",
        len(filtered_nodes),
        len(nodes),
        exam_id,
        top_k,
        score_threshold,
    )

    return "\n\n---\n\n".join(context_parts)


async def query_for_grading(
    exam_id: UUID,
    question_text: str,
    student_answer: str,
    max_score: float,
) -> dict:
    """Retrieve relevant context and call LLM to grade a single answer.

    Args:
        exam_id:        Exam UUID — ใช้ filter Qdrant ด้วย metadata
        question_text:  ข้อความคำถามของข้อสอบ
        student_answer: คำตอบของนักเรียนสำหรับข้อนี้
        max_score:      คะแนนเต็มของข้อนี้

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

        # 3. Call Groq LLM with retry on rate limit / timeout
        llm = _get_groq_llm()
        raw_response = await _call_llm_with_retry(
            llm, [ChatMessage(role="user", content=prompt)]
        )

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
