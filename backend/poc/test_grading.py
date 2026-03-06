"""
PoC: Groq API (llama-3.3-70b-versatile) — Thai essay grading test

Validates:
  - Groq API connection works
  - llama-3.3-70b can grade a Thai essay question
  - JSON response is parseable

Prerequisites:
  1. Copy backend/.env.example → backend/.env
  2. Set GROQ_API_KEY in .env
  3. pip install -r requirements.txt
  4. python poc/test_grading.py

Expected output: ✅ PoC passed!
"""
import json
import os
import re
import sys

# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load .env from backend/
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from llama_index.core.llms import ChatMessage
from llama_index.llms.groq import Groq

# ── Sample exam data ──────────────────────────────────────────────────────────

QUESTION = "อธิบายกระบวนการสังเคราะห์แสง และความสำคัญต่อระบบนิเวศ (10 คะแนน)"

MAX_SCORE = 10.0

RUBRIC = """
เกณฑ์การให้คะแนน:
- อธิบายวัตถุดิบที่ต้องการ (แสง, CO₂, น้ำ): 3 คะแนน
- อธิบายผลผลิต (กลูโคส, ออกซิเจน): 3 คะแนน
- อธิบายความสำคัญต่อระบบนิเวศ (ห่วงโซ่อาหาร, ออกซิเจนในบรรยากาศ): 4 คะแนน
"""

STUDENT_ANSWER = """
การสังเคราะห์แสงเป็นกระบวนการที่พืชสีเขียวใช้พลังงานจากแสงอาทิตย์
เพื่อเปลี่ยนคาร์บอนไดออกไซด์และน้ำให้เป็นกลูโคสและออกซิเจน
กระบวนการนี้มีความสำคัญมากเพราะทำให้มีออกซิเจนสำหรับสิ่งมีชีวิตทุกชนิด
และเป็นจุดเริ่มต้นของห่วงโซ่อาหารในระบบนิเวศ
"""

GRADING_PROMPT = """\
คุณเป็นผู้ช่วยตรวจข้อสอบที่แม่นยำและยุติธรรม

คำถาม: {question}
คะแนนเต็ม: {max_score}

เกณฑ์การให้คะแนน:
{rubric}

คำตอบนักเรียน:
{student_answer}

ให้ตรวจคำตอบตามเกณฑ์และตอบกลับเป็น JSON เท่านั้น (ไม่ต้องมีข้อความอื่น):
{{
  "score": <คะแนนที่ได้ เป็นตัวเลขทศนิยม>,
  "reasoning": "<เหตุผลการให้คะแนน อธิบายว่าตอบถูกหรือผิดและขาดอะไร>",
  "strengths": "<จุดเด่นของคำตอบ>",
  "improvements": "<สิ่งที่ควรเพิ่มหรือปรับปรุง>"
}}"""


def parse_json_from_response(text: str) -> dict:
    """Extract JSON object from LLM response text."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Fallback: extract first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No valid JSON found in response:\n{text}")


def main() -> None:
    print("=" * 60)
    print("PoC: Groq API — Thai Exam Grading (llama-3.3-70b)")
    print("=" * 60)

    # 1. Check API key
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key.startswith("gsk_your"):
        print("\n❌  GROQ_API_KEY not set in .env")
        print("    1. Copy backend/.env.example → backend/.env")
        print("    2. Set GROQ_API_KEY=gsk_<your-key> from https://console.groq.com")
        sys.exit(1)
    print(f"\n[1] API key loaded (***{api_key[-6:]})")

    # 2. Init Groq LLM
    print("\n[2] Initializing Groq llama-3.3-70b-versatile...")
    llm = Groq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.1,
        max_tokens=1024,
    )
    print("    LLM ready")

    # 3. Build prompt
    prompt = GRADING_PROMPT.format(
        question=QUESTION,
        max_score=MAX_SCORE,
        rubric=RUBRIC,
        student_answer=STUDENT_ANSWER,
    )

    # 4. Call LLM
    print("\n[3] Sending grading request to Groq...")
    response = llm.chat([ChatMessage(role="user", content=prompt)])
    raw = response.message.content
    print(f"    Response received ({len(raw)} chars)")

    print("\n--- Raw LLM response ---")
    print(raw)
    print("------------------------")

    # 5. Parse result
    print("\n[4] Parsing JSON result...")
    result = parse_json_from_response(raw)

    score = float(result["score"])
    print(f"\n    Score      : {score} / {MAX_SCORE}")
    print(f"    Reasoning  : {result.get('reasoning', '')[:120]}...")
    print(f"    Strengths  : {result.get('strengths', '')[:80]}...")
    print(f"    Improvements: {result.get('improvements', '')[:80]}...")

    # 6. Validate
    assert 0 <= score <= MAX_SCORE, f"Score {score} out of range [0, {MAX_SCORE}]"
    assert "reasoning" in result, "Missing 'reasoning' key"
    print(f"\n    ✓ Score is within valid range [0, {MAX_SCORE}]")
    print("    ✓ JSON parsed correctly with all required fields")

    print("\n" + "=" * 60)
    print("✅  PoC PASSED — Groq API grading working correctly")
    print("=" * 60)


if __name__ == "__main__":
    main()
