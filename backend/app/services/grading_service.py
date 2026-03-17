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

import asyncio
import logging
import re
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.database import get_supabase, maybe_single_safe
from app.services import rag_service

logger = logging.getLogger(__name__)

# ── Answer splitting ───────────────────────────────────────────────────────────

# Patterns that mark the start of a new question answer in Thai/English student scripts
_QUESTION_PATTERNS = [
    # "ข้อที่ 1" / "ข้อที่1" / "ข้อ 1" / "ข้อ1"
    r"ข้อที่?\s*(\d+)",
    # "คำถามที่ 1" / "คำถามที่1"
    r"คำถามที่\s*(\d+)",
    # "Question 1" / "Q1" / "Q.1"
    r"(?:Question|Q)\.?\s*(\d+)",
    # Plain "1." or "1)" at the start of a line
    r"^(\d+)[.)]\s",
]

_COMBINED_PATTERN = re.compile(
    "|".join(f"(?:{p})" for p in _QUESTION_PATTERNS),
    re.IGNORECASE | re.MULTILINE,
)


def split_answer_by_question(
    text: str,
    num_questions: int,
) -> dict[int, str]:
    """Split student answer text into per-question segments.

    Strategy:
      1. Regex: detect "ข้อ 1", "ข้อที่ 1", "Question 1", "1.", etc.
      2. If splitting fails / question count mismatch → return full text for every question.

    Returns:
        {question_number: answer_text}  (1-indexed)
    """
    if not text or not text.strip():
        return {n: "" for n in range(1, num_questions + 1)}

    # Find all matches with their positions and captured numbers
    matches = list(_COMBINED_PATTERN.finditer(text))

    # Extract (position, question_number) pairs, ignoring non-digit captures
    boundaries: list[tuple[int, int]] = []
    for m in matches:
        # Groups may be None for non-matching alternatives
        for grp in m.groups():
            if grp is not None:
                try:
                    q_num = int(grp)
                    if 1 <= q_num <= num_questions:
                        boundaries.append((m.start(), q_num))
                except ValueError:
                    pass
                break  # Only take first non-None group per match

    # Deduplicate: keep only the first occurrence per question number
    seen: set[int] = set()
    unique_boundaries: list[tuple[int, int]] = []
    for pos, qnum in boundaries:
        if qnum not in seen:
            seen.add(qnum)
            unique_boundaries.append((pos, qnum))

    # If we found all question boundaries, slice the text
    if len(unique_boundaries) == num_questions:
        result: dict[int, str] = {}
        for i, (pos, qnum) in enumerate(unique_boundaries):
            end = (
                unique_boundaries[i + 1][0]
                if i + 1 < len(unique_boundaries)
                else len(text)
            )
            result[qnum] = text[pos:end].strip()
        return result

    # Fallback: couldn't split reliably → assign entire text to every question
    logger.warning(
        "split_answer_by_question: expected %d questions, found %d boundaries — using full text fallback",
        num_questions,
        len(unique_boundaries),
    )
    return {n: text.strip() for n in range(1, num_questions + 1)}


# ── Grading orchestration ─────────────────────────────────────────────────────

_BACKOFF_SECONDS = [1, 2, 4, 8, 16]  # exponential backoff for rate-limited retries


async def _grade_with_backoff(
    exam_id: UUID,
    question_text: str,
    student_answer: str,
    max_score: float,
    retries: int = 5,
) -> dict:
    """Call rag_service.query_for_grading with exponential backoff on HTTP 429."""
    for attempt, wait in enumerate(_BACKOFF_SECONDS[:retries], start=1):
        try:
            return await rag_service.query_for_grading(
                exam_id=exam_id,
                question_text=question_text,
                student_answer=student_answer,
                max_score=max_score,
            )
        except Exception as exc:
            msg = str(exc).lower()
            is_rate_limit = "429" in msg or "rate limit" in msg or "too many" in msg
            if is_rate_limit and attempt < retries:
                logger.warning(
                    "Rate limited — retrying in %ds (attempt %d/%d)",
                    wait,
                    attempt,
                    retries,
                )
                await asyncio.sleep(wait)
            else:
                raise
    raise RuntimeError("Exhausted retries for grading")


async def start_grading(exam_id: UUID) -> None:
    """Trigger background grading for all ungraded submissions in an exam.

    Meant to be called via FastAPI BackgroundTasks.
    """
    supabase = get_supabase()
    logger.info("start_grading: exam_id=%s", exam_id)

    # ── 1. Fetch exam questions ────────────────────────────────────────────────
    questions_resp = (
        supabase.table("exam_questions")
        .select("id, question_number, question_text, max_score")
        .eq("exam_id", str(exam_id))
        .order("question_number")
        .execute()
    )
    questions = questions_resp.data or []
    if not questions:
        logger.warning("start_grading: no questions found for exam %s", exam_id)
        return

    num_questions = len(questions)

    # ── 2. Fetch submissions that are in 'parsed' state ────────────────────────
    subs_resp = (
        supabase.table("student_submissions")
        .select("id, parsed_text, status")
        .eq("exam_id", str(exam_id))
        .in_("status", ["parsed", "uploaded"])
        .execute()
    )
    submissions = subs_resp.data or []
    if not submissions:
        logger.info("start_grading: no eligible submissions for exam %s", exam_id)
        return

    # ── 3. Grade each submission ───────────────────────────────────────────────
    for sub in submissions:
        sub_id = sub["id"]
        parsed_text = sub.get("parsed_text") or ""

        # Mark submission as grading
        supabase.table("student_submissions").update({"status": "grading"}).eq(
            "id", sub_id
        ).execute()

        answer_map = split_answer_by_question(parsed_text, num_questions)

        graded_ok = True
        for q in questions:
            q_id = q["id"]
            q_num = q["question_number"]
            q_text = q["question_text"]
            max_score = float(q["max_score"])
            student_answer = answer_map.get(q_num, "")

            try:
                result = await _grade_with_backoff(
                    exam_id=exam_id,
                    question_text=q_text,
                    student_answer=student_answer,
                    max_score=max_score,
                )
                llm_score = result["score"]
                reasoning = result["reasoning"]

                # Upsert grading result (avoid duplicates on re-run)
                existing = maybe_single_safe(
                    supabase.table("grading_results")
                    .select("id")
                    .eq("submission_id", sub_id)
                    .eq("question_id", q_id)
                )
                if existing.data:
                    supabase.table("grading_results").update(
                        {
                            "student_answer_text": student_answer,
                            "llm_score": llm_score,
                            "llm_max_score": max_score,
                            "llm_reasoning": reasoning,
                            "llm_model_used": "llm",
                            "status": "pending",
                            "expert_score": None,
                            "expert_feedback": None,
                        }
                    ).eq("id", existing.data["id"]).execute()
                else:
                    now = datetime.now(timezone.utc).isoformat()
                    supabase.table("grading_results").insert(
                        {
                            "id": str(uuid4()),
                            "submission_id": sub_id,
                            "question_id": q_id,
                            "student_answer_text": student_answer,
                            "llm_score": llm_score,
                            "llm_max_score": max_score,
                            "llm_reasoning": reasoning,
                            "llm_model_used": "llm",
                            "status": "pending",
                            "expert_score": None,
                            "expert_feedback": None,
                            "created_at": now,
                        }
                    ).execute()

            except Exception as exc:
                logger.exception(
                    "Grading failed for submission=%s question=%s: %s",
                    sub_id,
                    q_id,
                    exc,
                )
                graded_ok = False

        # Mark submission status
        new_status = (
            "graded" if graded_ok else "parsed"
        )  # revert to parsed so it can be retried
        supabase.table("student_submissions").update({"status": new_status}).eq(
            "id", sub_id
        ).execute()
        logger.info("start_grading: submission %s → %s", sub_id, new_status)

    logger.info("start_grading: completed for exam %s", exam_id)
