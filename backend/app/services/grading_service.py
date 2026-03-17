"""
Grading Service — orchestrate background grading pipeline.
BE-S responsibility (Sprint 3).
Sprint 4: Graceful error handling, structured logging, per-question error recovery.
"""

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.database import db
from app.services.rag_service import query_for_grading
from app.config import get_settings
from app.core.exceptions import LLMException, GroqTimeoutException

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
    errors: list[str] = field(default_factory=list)  # Sprint 4: เก็บ error details


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


def is_grading_running(exam_id: uuid.UUID) -> bool:
    """Check if grading is currently running for an exam."""
    progress = _grading_progress.get(exam_id)
    return progress is not None and progress.status == "running"


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

    # Fallback: distribute paragraphs across questions evenly
    logger.warning("Regex split failed, using paragraph-distribution fallback")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]

    if not paragraphs:
        return {1: text}

    if len(paragraphs) >= num_questions:
        # Distribute paragraphs as evenly as possible across questions
        parts: dict[int, str] = {}
        base, extra = divmod(len(paragraphs), num_questions)
        idx = 0
        for q in range(num_questions):
            count = base + (1 if q < extra else 0)
            chunk = paragraphs[idx : idx + count]
            parts[q + 1] = "\n\n".join(chunk)
            idx += count
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
    Sprint 4: เพิ่ม timeout handling สำหรับ LLM call
    """
    from llama_index.llms.groq import Groq
    from llama_index.core.llms import ChatMessage

    settings = get_settings()
    llm = Groq(
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=4096,
        request_timeout=settings.llm_request_timeout,
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

    except asyncio.TimeoutError:
        logger.error(f"LLM split timed out for exam {exam_id}")
        raise GroqTimeoutException(settings.llm_request_timeout)
    except Exception as e:
        error_str = str(e).lower()
        if "timeout" in error_str or "timed out" in error_str:
            logger.error(f"LLM split timed out for exam {exam_id}: {e}")
            raise GroqTimeoutException(settings.llm_request_timeout) from e
        logger.error(f"LLM split failed: {e}")
        raise LLMException(f"Failed to split answer by LLM: {e}") from e


# ── Main grading orchestration ──────────────────────────────────────────────────


async def start_grading(exam_id: uuid.UUID) -> None:
    """Trigger background grading for all ungraded submissions in an exam.

    Sprint 4: Graceful error handling improvements:
      - Per-question error recovery (ข้อที่ grade ไม่สำเร็จจะถูกข้ามไป ไม่ทำให้ submission ทั้งหมดล้มเหลว)
      - Timeout handling สำหรับ Groq API
      - Structured logging ทุกขั้นตอน
      - เก็บ error details ใน progress สำหรับ debugging

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
            logger.error("Grading failed for exam %s: no questions", exam_id)
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
            logger.info("No submissions to grade for exam %s", exam_id)
            return

        progress.total = len(submissions)
        logger.info(
            "Starting grading for %d submissions, %d questions (exam=%s)",
            len(submissions),
            num_questions,
            exam_id,
        )

        # 3. Grade each submission
        for submission in submissions:
            submission_errors: list[str] = []
            graded_count = 0

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
                logger.info(
                    "Grading submission for student '%s' (submission=%s)",
                    student_name,
                    submission.id,
                )

                # Split answer text by question
                parsed_text = submission.parsedText or ""

                if not parsed_text.strip():
                    logger.warning(
                        "Empty parsed text for submission %s, skipping",
                        submission.id,
                    )
                    submission_errors.append(
                        "Empty parsed text — ไม่มีข้อความในไฟล์ที่ parse ได้"
                    )
                    await db.studentsubmission.update(
                        where={"id": submission.id},
                        data={"status": "graded"},
                    )
                    progress.completed += 1
                    continue

                answers = split_answer_by_question(parsed_text, num_questions)

                # If split failed, try LLM fallback
                if len(answers) < num_questions:
                    logger.warning(
                        "Split returned %d parts (expected %d), trying LLM fallback",
                        len(answers),
                        num_questions,
                    )
                    try:
                        answers = await split_answer_by_llm(
                            parsed_text, num_questions, exam_id
                        )
                    except (LLMException, GroqTimeoutException) as e:
                        err_msg = f"LLM split fallback failed: {e.message}"
                        logger.error(err_msg)
                        submission_errors.append(err_msg)
                        # ใช้ answers เดิมจาก regex split ต่อไป ไม่ให้ fail ทั้งหมด

                # Grade each question — per-question error recovery
                for question in questions:
                    question_num = question.questionNumber
                    student_answer = answers.get(question_num, "")

                    # Skip if no answer for this question
                    if not student_answer.strip():
                        logger.info(
                            "No answer for Q%d (student=%s), saving score=0",
                            question_num,
                            student_name,
                        )
                        # Sprint 4: บันทึก score=0 สำหรับข้อที่ไม่มีคำตอบ แทนที่จะข้ามไป
                        try:
                            await db.gradingresult.create(
                                data={
                                    "id": str(uuid.uuid4()),
                                    "submissionId": submission.id,
                                    "questionId": question.id,
                                    "studentAnswerText": "(ไม่มีคำตอบ)",
                                    "llmScore": 0.0,
                                    "llmMaxScore": question.maxScore,
                                    "llmReasoning": "ไม่พบคำตอบของนักเรียนสำหรับข้อนี้",
                                    "llmModelUsed": settings.llm_model,
                                    "status": "pending_review",
                                    "gradedAt": datetime.now(timezone.utc),
                                }
                            )
                        except Exception as save_err:
                            logger.error(
                                "Failed to save empty answer result: %s", save_err
                            )
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
                        await db.gradingresult.create(
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
                                "gradedAt": datetime.now(timezone.utc),
                            }
                        )

                        graded_count += 1
                        logger.debug(
                            "Graded Q%d for %s: %.1f/%s",
                            question_num,
                            student_name,
                            result["score"],
                            question.maxScore,
                        )

                    except GroqTimeoutException as e:
                        # Sprint 4: Timeout — บันทึก score=0 พร้อมเหตุผล แล้วไปข้อถัดไป
                        err_msg = f"Q{question_num} timeout: {e.message}"
                        logger.error(err_msg)
                        submission_errors.append(err_msg)
                        try:
                            await db.gradingresult.create(
                                data={
                                    "id": str(uuid.uuid4()),
                                    "submissionId": submission.id,
                                    "questionId": question.id,
                                    "studentAnswerText": student_answer,
                                    "llmScore": 0.0,
                                    "llmMaxScore": question.maxScore,
                                    "llmReasoning": f"ให้คะแนน 0 เนื่องจากระบบขัดข้อง: {e.message}",
                                    "llmModelUsed": settings.llm_model,
                                    "status": "pending_review",
                                    "gradedAt": datetime.now(timezone.utc),
                                }
                            )
                        except Exception as save_err:
                            logger.error("Failed to save timeout result: %s", save_err)
                        progress.failed += 1
                        continue

                    except LLMException as e:
                        # Sprint 4: LLM error — บันทึก score=0 พร้อมเหตุผล แล้วไปข้อถัดไป
                        err_msg = f"Q{question_num} LLM error: {e.message}"
                        logger.error(err_msg)
                        submission_errors.append(err_msg)
                        try:
                            await db.gradingresult.create(
                                data={
                                    "id": str(uuid.uuid4()),
                                    "submissionId": submission.id,
                                    "questionId": question.id,
                                    "studentAnswerText": student_answer,
                                    "llmScore": 0.0,
                                    "llmMaxScore": question.maxScore,
                                    "llmReasoning": f"ให้คะแนน 0 เนื่องจากระบบขัดข้อง: {e.message}",
                                    "llmModelUsed": settings.llm_model,
                                    "status": "pending_review",
                                    "gradedAt": datetime.now(timezone.utc),
                                }
                            )
                        except Exception as save_err:
                            logger.error("Failed to save LLM error result: %s", save_err)
                        progress.failed += 1
                        continue

                    except Exception as e:
                        err_msg = f"Q{question_num} unexpected error: {str(e)}"
                        logger.error(err_msg, exc_info=True)
                        submission_errors.append(err_msg)
                        try:
                            await db.gradingresult.create(
                                data={
                                    "id": str(uuid.uuid4()),
                                    "submissionId": submission.id,
                                    "questionId": question.id,
                                    "studentAnswerText": student_answer,
                                    "llmScore": 0.0,
                                    "llmMaxScore": question.maxScore,
                                    "llmReasoning": f"ให้คะแนน 0 เนื่องจากระบบขัดข้อง: {str(e)}",
                                    "llmModelUsed": settings.llm_model,
                                    "status": "pending_review",
                                    "gradedAt": datetime.now(timezone.utc),
                                }
                            )
                        except Exception as save_err:
                            logger.error("Failed to save error result: %s", save_err)
                        progress.failed += 1
                        continue

                # Mark submission as graded (แม้จะมีบาง question ที่ fail)
                final_status = "graded" if graded_count > 0 else "failed"
                await db.studentsubmission.update(
                    where={"id": submission.id},
                    data={"status": final_status},
                )

                progress.completed += 1

                if submission_errors:
                    progress.errors.extend(submission_errors)
                    logger.warning(
                        "Graded submission %s with %d errors: %d/%d questions succeeded",
                        submission.id,
                        len(submission_errors),
                        graded_count,
                        num_questions,
                    )
                else:
                    logger.info(
                        "Graded submission %d/%d (%s): all %d questions OK",
                        progress.completed,
                        len(submissions),
                        student_name,
                        graded_count,
                    )

            except Exception as e:
                err_msg = f"Submission {submission.id} failed: {str(e)}"
                logger.error(err_msg, exc_info=True)
                progress.failed += 1
                progress.errors.append(err_msg)

                # Mark submission as failed
                try:
                    await db.studentsubmission.update(
                        where={"id": submission.id},
                        data={"status": "failed"},
                    )
                except Exception:
                    pass
                continue

        # 4. Finalize
        progress.status = "completed"
        logger.info(
            "Grading completed for exam %s: %d/%d success, %d question-level failures, %d errors",
            exam_id,
            progress.completed,
            progress.total,
            progress.failed,
            len(progress.errors),
        )

    except Exception as e:
        logger.error("Grading failed for exam %s: %s", exam_id, e, exc_info=True)
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
        completed = len([s for s in submissions if s.status in ("graded", "failed")])

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
