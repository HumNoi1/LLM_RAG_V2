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
import json
import logging
import re
from uuid import UUID

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.llms import ChatMessage
from llama_index.llms.groq import Groq
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import get_settings
from app.core.exceptions import LLMException
from app.services.embedding_service import _get_embed_model, _get_qdrant_client

logger = logging.getLogger(__name__)

# Grading prompt — Thai language, instructs the LLM to return pure JSON
_GRADING_PROMPT = """\
คุณเป็นผู้ช่วยตรวจข้อสอบที่แม่นยำและยุติธรรม

คำถาม: {question}
คะแนนเต็ม: {max_score}

เนื้อหาอ้างอิง (เฉลย / Rubric / เนื้อหาวิชา):
{context}

คำตอบนักเรียน:
{student_answer}

ให้ตรวจคำตอบตามเกณฑ์และตอบกลับเป็น JSON เท่านั้น (ไม่ต้องมีข้อความอื่น):
{{
  "score": <คะแนนที่ได้ เป็นตัวเลขทศนิยม ไม่เกิน {max_score}>,
  "reasoning": "<เหตุผลการให้คะแนน อธิบายว่าตอบถูกหรือผิดและขาดอะไร>"
}}"""


def _parse_json_from_llm(text: str) -> dict:
    """Extract JSON object from LLM response text."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Fallback: strip markdown code fences then try again
    cleaned = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Last resort: extract first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No valid JSON found in LLM response:\n{text[:300]}")


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
        dict with keys: score (float), reasoning (str)

    Raises:
        LLMException: on Groq API or JSON parsing error.
    """
    settings = get_settings()

    try:
        # ── 1. Build Qdrant-backed retriever filtered by exam_id ──────────────
        embed_model = _get_embed_model()
        client: QdrantClient = _get_qdrant_client()
        collection = settings.qdrant_collection_name

        Settings.embed_model = embed_model

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection,
        )
        index = VectorStoreIndex.from_vector_store(vector_store)

        # Filter by exam_id — fetch top-5 most relevant chunks
        retriever = index.as_retriever(
            similarity_top_k=5,
            filters={
                "filters": [
                    {"key": "exam_id", "value": str(exam_id), "operator": "=="}
                ]
            },
        )
        nodes = retriever.retrieve(question_text)
        context_chunks = [node.text for node in nodes]
        context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(ไม่มีเอกสารอ้างอิง)"

        # ── 2. Build grading prompt ────────────────────────────────────────────
        prompt = _GRADING_PROMPT.format(
            question=question_text,
            max_score=max_score,
            context=context,
            student_answer=student_answer,
        )

        # ── 3. Call Groq LLM ───────────────────────────────────────────────────
        llm = Groq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        response = llm.chat([ChatMessage(role="user", content=prompt)])
        raw = response.message.content

        # ── 4. Parse JSON response ─────────────────────────────────────────────
        result = _parse_json_from_llm(raw)
        score = float(result["score"])
        # Clamp score to [0, max_score]
        score = max(0.0, min(float(max_score), score))
        reasoning = str(result.get("reasoning", ""))

        logger.debug(
            "query_for_grading exam=%s score=%.2f/%.2f",
            exam_id, score, max_score,
        )
        return {"score": score, "reasoning": reasoning}

    except LLMException:
        raise
    except Exception as exc:
        logger.exception("query_for_grading failed for exam=%s: %s", exam_id, exc)
        raise LLMException(str(exc)) from exc
