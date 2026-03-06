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
from uuid import UUID


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

    Sprint 2 implementation.
    """
    raise NotImplementedError("rag_service.query_for_grading — implement in Sprint 2")
