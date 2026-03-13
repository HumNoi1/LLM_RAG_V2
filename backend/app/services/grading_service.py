import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.database import db
from app.services.rag_service import query_for_grading
from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Grading progress tracking (in-memory) ──────────────────────────────────────


@dataclass
class GradingProgress:
    exam_id: uuid.UUID
    total: int = 0
    completed: int = 0
    failed: int = 0
    status: str = "idle"
    error_message: Optional[str] = None


_grading_progress: dict[uuid.UUID, GradingProgress] = {}


def get_grading_progress(exam_id: uuid.UUID) -> GradingProgress:
    """Get or create grading progress for an exam."""
    if exam_id not in _grading_progress:
        _grading_progress[exam_id] = GradingProgress(exam_id=exam_id)
    return _grading_progress[exam_id]


def reset_grading_progress(exam_id: uuid.UUID) -> GradingProgress:
    """Reset grading progress for a new grading run."""
    _grading_progress[exam_id] = GradingProgress(exam_id=exam_id, status="running")
    return _grading_progress[exam_id]


# ── Student answer splitting ────────────────────────────────────────────────────


def split_answer_by_question(
    text: str,
    num_questions: int,
) -> dict[int, str]:
    """Split student answer text into per-question segments.

    Strategy:
      1. Regex: detect "ข้อ 1", "ข้อที่ 1", "Question 1", "1.", "1)", etc.
      2. If splitting fails / question count mismatch → simple equal split fallback.

    Returns:
        {question_number: answer_text}
    """
    if not text or num_questions <= 0:
        return {}

    # Clean up text
    text = text.strip()

    # Thai patterns: ข้อ 1, ข้อที่ 1, ข้อ ๑
    # English patterns: Question 1, 1., 1), Q1
    patterns = [
        r"ข้อที่\s*(\d+)",
        r"ข้อ\s*(\d+)",
        r"Question\s*(\d+)",
        r"Q\.?\s*(\d+)",
        r"(\d+)\.",
        r"(\d+)\)",
    ]

    # Try each pattern to find question boundaries
    for pattern in patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if len(matches) >= 2:
            # Found multiple question markers
            parts: dict[int, str] = {}
            for i, match in enumerate(matches):
                q_num = int(match.group(1))
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                answer = text[start:end].strip()
                if answer:
                    parts[q_num] = answer

            if len(parts) >= num_questions:
                logger.info(f"Split by pattern '{pattern}': {len(parts)} parts")
                return parts

    # Fallback: simple equal split by newlines or paragraphs
    logger.warning("Regex split failed, using equal split fallback")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) >= num_questions:
        avg_len = len(text) // num_questions
        parts = {}
        for i in range(num_questions):
            start = i * avg_len
            end = start + avg_len if i < num_questions - 1 else len(text)
            parts[i + 1] = text[start:end].strip()
        return parts

    # Last resort: return whole text as answer for question 1
    logger.warning(f"Could not split answers, assigning whole text to Q1")
    return {1: text}


async def split_answer_by_llm(
    text: str,
    num_questions: int,
    exam_id: uuid.UUID,
) -> dict[int, str]:
    """Fallback: Use LLM to split student answer by questions.

    This is more expensive but handles complex formats.
    """
    from llama_index.llms.groq import Groq
    from llama_index.core.llms import ChatMessage
    from app.core.exceptions import LLMException

    settings = get_settings()
    llm = Groq(
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=4096,
    )

    prompt = f"""แยกคำตอบของนักเรียนออกเป็น {num_questions} ข้อ ตอบเป็น JSON เท่านั้น:

{{
  "1": "<คำตอบข้อ 1>",
  "2": "<คำตอบข้อ 2>",
  ...
}}

คำตอบนักเรียน:
{text}

ตอบเป็น JSON เท่านั้น:"""

    try:
        response = asyncio.to_thread(
            llm.chat, [ChatMessage(role="user", content=prompt)]
        )
        response = await response
        import json

        result = json.loads(response.message.content.strip())
        return {int(k): v for k, v in result.items()}
    except Exception as e:
        logger.error(f"LLM split failed: {e}")
        raise LLMException(f"Failed to split answer by LLM: {e}") from e


# ── Main grading orchestration ──────────────────────────────────────────────────


async def start_grading(exam_id: uuid.UUID) -> None:
    """Trigger background grading for all ungraded submissions in an exam.

    Flow:
      1. Fetch all submissions with status 'parsed' for this exam
      2. Fetch all questions for this exam
      3. For each submission:
         a. Split parsed_text by question
         b. For each question: RAG query → LLM grading → save result
         c. Update submission status → 'graded'
      4. Update progress counter
    """
    progress = reset_grading_progress(exam_id)
    settings = get_settings()

    try:
        # 1. Fetch exam questions
        questions = await db.examquestion.find_many(
            where={"examId": str(exam_id)},
            order_by={"questionNumber": "asc"},
        )

        if not questions:
            progress.status = "failed"
            progress.error_message = "No questions found for this exam"
            logger.error(f"Grading failed for exam {exam_id}: no questions")
            return

        num_questions = len(questions)

        # 2. Fetch submissions with status 'parsed'
        submissions = await db.studentsubmission.find_many(
            where={
                "examId": str(exam_id),
                "status": "parsed",
            }
        )

        if not submissions:
            progress.status = "completed"
            progress.total = 0
            progress.completed = 0
            logger.info(f"No submissions to grade for exam {exam_id}")
            return

        progress.total = len(submissions)
        logger.info(
            f"Starting grading for {len(submissions)} submissions, {num_questions} questions"
        )

        # 3. Grade each submission
        for submission in submissions:
            try:
                # Update submission status to grading
                await db.studentsubmission.update(
                    where={"id": submission.id},
                    data={"status": "grading"},
                )

                # Get student (handle None case)
                student = await db.student.find_unique(
                    where={"id": submission.studentId}
                )
                student_name = student.fullName if student else "Unknown"

                # Split answer text by question
                parsed_text = submission.parsedText or ""
                answers = split_answer_by_question(parsed_text, num_questions)

                # If split failed, try LLM fallback
                if len(answers) < num_questions:
                    logger.warning(
                        f"Split returned {len(answers)} parts, trying LLM fallback"
                    )
                    try:
                        answers = await split_answer_by_llm(
                            parsed_text, num_questions, exam_id
                        )
                    except Exception as e:
                        logger.error(f"LLM split fallback failed: {e}")

                # Grade each question
                for question in questions:
                    question_num = question.questionNumber
                    student_answer = answers.get(question_num, "")

                    # Skip if no answer for this question
                    if not student_answer.strip():
                        logger.info(f"No answer for Q{question_num}, skipping")
                        continue

                    try:
                        # Call RAG + LLM grading
                        result = await query_for_grading(
                            exam_id=exam_id,
                            question_text=question.questionText,
                            student_answer=student_answer,
                            max_score=question.maxScore,
                        )

                        # Save grading result
                        grading_result = await db.gradingresult.create(
                            data={
                                "id": str(uuid.uuid4()),
                                "submissionId": submission.id,
                                "questionId": question.id,
                                "studentAnswerText": student_answer,
                                "llmScore": result["score"],
                                "llmMaxScore": question.maxScore,
                                "llmReasoning": result["reasoning"],
                                "llmModelUsed": settings.llm_model,
                                "status": "pending_review",
                                "gradedAt": datetime.utcnow(),
                            }
                        )

                        logger.debug(
                            f"Graded Q{question_num} for {student_name}: {result['score']}/{question.maxScore}"
                        )

                    except Exception as e:
                        logger.error(f"Failed to grade Q{question_num}: {e}")
                        progress.failed += 1
                        continue

                # Mark submission as graded
                await db.studentsubmission.update(
                    where={"id": submission.id},
                    data={"status": "graded"},
                )

                progress.completed += 1
                logger.info(
                    f"Graded submission {progress.completed}/{len(submissions)}"
                )

            except Exception as e:
                logger.error(f"Failed to grade submission {submission.id}: {e}")
                progress.failed += 1
                # Mark submission as graded anyway to not block (with failed status)
                try:
                    await db.studentsubmission.update(
                        where={"id": submission.id},
                        data={"status": "graded"},
                    )
                except Exception:
                    pass
                continue

        # 4. Finalize
        progress.status = "completed"
        logger.info(
            f"Grading completed for exam {exam_id}: {progress.completed} success, {progress.failed} failed"
        )

    except Exception as e:
        logger.error(f"Grading failed for exam {exam_id}: {e}")
        progress.status = "failed"
        progress.error_message = str(e)
        raise


# ── Progress endpoint helpers ──────────────────────────────────────────────────


async def get_grading_status(exam_id: uuid.UUID) -> dict:
    """Get grading status for an exam."""
    progress = get_grading_progress(exam_id)

    # If no grading started yet, check DB for graded submissions
    if progress.status == "idle":
        submissions = await db.studentsubmission.find_many(
            where={"examId": str(exam_id)}
        )
        total = len(submissions)
        completed = len([s for s in submissions if s.status == "graded"])

        if total == 0:
            return {
                "exam_id": exam_id,
                "status": "idle",
                "total_submissions": 0,
                "completed": 0,
                "failed": 0,
                "progress_percent": 0.0,
            }

        return {
            "exam_id": exam_id,
            "status": "completed" if completed == total else "running",
            "total_submissions": total,
            "completed": completed,
            "failed": 0,
            "progress_percent": round((completed / total) * 100, 1)
            if total > 0
            else 0.0,
        }

    if progress.total and progress.total > 0:
        total = progress.total
    else:
        total = 1

    return {
        "exam_id": exam_id,
        "status": progress.status,
        "total_submissions": progress.total,
        "completed": progress.completed,
        "failed": progress.failed,
        "progress_percent": round((progress.completed / total) * 100, 1)
        if total > 0
        else 0.0,
    }
