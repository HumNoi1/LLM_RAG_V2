"""
Grading Service — orchestrate full grading pipeline for an exam.
BE-S responsibility (Sprint 3).

Flow:
  For each student_submission in exam:
    1. Split parsed_text by question (regex "ข้อ N" / "Question N" + LLM fallback)
    2. For each question:
       a. rag_service.query_for_grading(exam_id, question_text, answer, max_score)
       b. Save GradingResult to DB (status=pending)
    3. Update submission status → 'graded'
    4. Update grading progress counter

Rate limiting:
  - Groq free tier: 30 req/min for llama-3.3-70b
  - Use exponential backoff on HTTP 429
"""
from uuid import UUID


async def start_grading(exam_id: UUID) -> None:
    """Trigger background grading for all ungraded submissions in an exam.

    Meant to be called via FastAPI BackgroundTasks.
    Sprint 3 implementation.
    """
    raise NotImplementedError("grading_service.start_grading — implement in Sprint 3")


def split_answer_by_question(
    text: str,
    num_questions: int,
) -> dict[int, str]:
    """Split student answer text into per-question segments.

    Strategy:
      1. Regex: detect "ข้อ 1", "ข้อที่ 1", "Question 1", "1.", etc.
      2. If splitting fails / question count mismatch → LLM fallback.

    Returns:
        {question_number: answer_text}

    Sprint 3 implementation.
    """
    raise NotImplementedError("grading_service.split_answer_by_question — implement in Sprint 3")
