"""
Integration tests — Sprint 1-2 API endpoints.

Runs against a **live** FastAPI server on http://127.0.0.1:8000.
Requires:
  - Server running (`uv run uvicorn app.main:app --port 8000`)
  - Supabase + Qdrant reachable
  - fpdf2 installed (for PDF generation)

Usage:
  uv run pytest tests/test_integration_api.py -v --tb=short -x
"""

import io
import time
import uuid

import pytest
import requests
from fpdf import FPDF

BASE = "http://127.0.0.1:8000/api/v1"
UNIQUE = uuid.uuid4().hex[:8]  # avoid collisions across runs


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_pdf(text: str = "Hello World") -> bytes:
    """Generate a minimal valid PDF in memory."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, text=text)
    return pdf.output()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def teacher():
    """Register + login a fresh teacher user; return dict with tokens & user info."""
    email = f"inttest_{UNIQUE}@test.com"
    password = "testpass1234"

    # Register
    r = requests.post(
        f"{BASE}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Integration Teacher {UNIQUE}",
            "role": "teacher",
        },
        timeout=10,
    )
    assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"
    user = r.json()

    # Login
    r2 = requests.post(
        f"{BASE}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    assert r2.status_code == 200, f"Login failed: {r2.status_code} {r2.text}"
    tokens = r2.json()

    return {
        "user_id": user["id"],
        "email": email,
        "password": password,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


def _auth(teacher_fixture) -> dict:
    """Return Authorization header dict."""
    return {"Authorization": f"Bearer {teacher_fixture['access_token']}"}


# ═════════════════════════════════════════════════════════════════════════════
#  AUTH
# ═════════════════════════════════════════════════════════════════════════════


class TestAuth:
    def test_register_duplicate(self, teacher):
        """Registering the same email again should return 409."""
        r = requests.post(
            f"{BASE}/auth/register",
            json={
                "email": teacher["email"],
                "password": "anything1234",
                "full_name": "Dup",
                "role": "teacher",
            },
            timeout=10,
        )
        assert r.status_code == 409

    def test_login_wrong_password(self, teacher):
        r = requests.post(
            f"{BASE}/auth/login",
            json={"email": teacher["email"], "password": "wrongpassword"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_me(self, teacher):
        r = requests.get(f"{BASE}/auth/me", headers=_auth(teacher), timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == teacher["email"]
        assert body["id"] == teacher["user_id"]

    def test_refresh(self, teacher):
        r = requests.post(
            f"{BASE}/auth/refresh",
            json={"refresh_token": teacher["refresh_token"]},
            timeout=10,
        )
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_me_no_token(self):
        r = requests.get(f"{BASE}/auth/me", timeout=10)
        assert r.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
#  EXAMS CRUD
# ═════════════════════════════════════════════════════════════════════════════


class TestExamCrud:
    @pytest.fixture(autouse=True)
    def _setup(self, teacher):
        self.teacher = teacher
        self.headers = _auth(teacher)

    def test_create_exam(self):
        r = requests.post(
            f"{BASE}/exams",
            json={
                "title": f"Integration Exam {UNIQUE}",
                "subject": "Science",
                "description": "Integration test exam",
                "total_questions": 3,
            },
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 201, f"Create exam: {r.status_code} {r.text}"
        body = r.json()
        assert body["title"] == f"Integration Exam {UNIQUE}"
        assert body["total_questions"] == 3
        assert body["created_by"] == self.teacher["user_id"]
        # Store for later tests
        self.__class__._exam_id = body["id"]

    def test_list_exams(self):
        r = requests.get(f"{BASE}/exams", headers=self.headers, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        assert isinstance(body["exams"], list)

    def test_get_exam(self):
        exam_id = getattr(self.__class__, "_exam_id", None)
        if not exam_id:
            pytest.skip("No exam_id from create test")
        r = requests.get(f"{BASE}/exams/{exam_id}", headers=self.headers, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == exam_id
        assert "questions" in body

    def test_update_exam(self):
        exam_id = getattr(self.__class__, "_exam_id", None)
        if not exam_id:
            pytest.skip("No exam_id from create test")
        r = requests.put(
            f"{BASE}/exams/{exam_id}",
            json={"title": f"Updated Exam {UNIQUE}"},
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["title"] == f"Updated Exam {UNIQUE}"

    def test_get_nonexistent_exam(self):
        fake_id = str(uuid.uuid4())
        r = requests.get(f"{BASE}/exams/{fake_id}", headers=self.headers, timeout=10)
        assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
#  QUESTIONS
# ═════════════════════════════════════════════════════════════════════════════


class TestQuestions:
    @pytest.fixture(autouse=True)
    def _setup(self, teacher):
        self.teacher = teacher
        self.headers = _auth(teacher)
        # Create a fresh exam for question tests
        if not getattr(self.__class__, "_q_exam_id", None):
            r = requests.post(
                f"{BASE}/exams",
                json={
                    "title": f"Q-Exam {UNIQUE}",
                    "subject": "Math",
                    "total_questions": 2,
                },
                headers=self.headers,
                timeout=10,
            )
            assert r.status_code == 201
            self.__class__._q_exam_id = r.json()["id"]

    def test_add_question(self):
        r = requests.post(
            f"{BASE}/exams/{self._q_exam_id}/questions",
            json={
                "question_number": 1,
                "question_text": "What is 2+2?",
                "max_score": 10.0,
            },
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 201, f"Add Q: {r.status_code} {r.text}"
        body = r.json()
        assert body["question_number"] == 1
        assert body["max_score"] == 10.0
        self.__class__._question_id = body["id"]

    def test_add_duplicate_question_number(self):
        """Adding question with same number should 409."""
        r = requests.post(
            f"{BASE}/exams/{self._q_exam_id}/questions",
            json={
                "question_number": 1,
                "question_text": "Duplicate",
                "max_score": 5.0,
            },
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 409

    def test_add_second_question(self):
        r = requests.post(
            f"{BASE}/exams/{self._q_exam_id}/questions",
            json={
                "question_number": 2,
                "question_text": "What is 3+3?",
                "max_score": 15.0,
            },
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 201

    def test_get_exam_with_questions(self):
        r = requests.get(
            f"{BASE}/exams/{self._q_exam_id}",
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 200
        body = r.json()
        assert len(body["questions"]) == 2
        # Verify sorted by question_number
        assert body["questions"][0]["question_number"] == 1
        assert body["questions"][1]["question_number"] == 2

    def test_update_question(self):
        q_id = getattr(self.__class__, "_question_id", None)
        if not q_id:
            pytest.skip("No question_id")
        r = requests.put(
            f"{BASE}/exams/{self._q_exam_id}/questions/{q_id}",
            json={"max_score": 20.0},
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 200
        assert r.json()["max_score"] == 20.0

    def test_delete_question(self):
        q_id = getattr(self.__class__, "_question_id", None)
        if not q_id:
            pytest.skip("No question_id")
        r = requests.delete(
            f"{BASE}/exams/{self._q_exam_id}/questions/{q_id}",
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 204


# ═════════════════════════════════════════════════════════════════════════════
#  DOCUMENT UPLOAD + LIST
# ═════════════════════════════════════════════════════════════════════════════


class TestDocuments:
    @pytest.fixture(autouse=True)
    def _setup(self, teacher):
        self.teacher = teacher
        self.headers = _auth(teacher)
        # Create an exam for document tests
        if not getattr(self.__class__, "_doc_exam_id", None):
            r = requests.post(
                f"{BASE}/exams",
                json={
                    "title": f"Doc-Exam {UNIQUE}",
                    "subject": "Biology",
                    "total_questions": 1,
                },
                headers=self.headers,
                timeout=10,
            )
            assert r.status_code == 201
            self.__class__._doc_exam_id = r.json()["id"]

    def test_upload_reference_pdf(self):
        pdf_bytes = _make_pdf("Answer key content for integration test")
        files = {"file": ("answer_key.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {
            "exam_id": self._doc_exam_id,
            "doc_type": "answer_key",
        }
        r = requests.post(
            f"{BASE}/documents/upload",
            files=files,
            data=data,
            headers=self.headers,
            timeout=15,
        )
        assert r.status_code == 202, f"Upload doc: {r.status_code} {r.text}"
        body = r.json()
        assert body["message"] == "Document uploaded. Embedding in progress."
        assert body["document"]["doc_type"] == "answer_key"
        assert body["document"]["embedding_status"] == "pending"
        self.__class__._doc_id = body["document"]["id"]

    def test_list_documents(self):
        r = requests.get(
            f"{BASE}/documents",
            params={"exam_id": self._doc_exam_id},
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        assert isinstance(body["documents"], list)

    def test_upload_non_pdf_rejected(self):
        files = {"file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")}
        data = {"exam_id": self._doc_exam_id, "doc_type": "answer_key"}
        r = requests.post(
            f"{BASE}/documents/upload",
            files=files,
            data=data,
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 422

    def test_upload_to_nonexistent_exam(self):
        pdf_bytes = _make_pdf("test")
        files = {"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {"exam_id": str(uuid.uuid4()), "doc_type": "answer_key"}
        r = requests.post(
            f"{BASE}/documents/upload",
            files=files,
            data=data,
            headers=self.headers,
            timeout=10,
        )
        assert r.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
#  EXAM DELETE (cascade)
# ═════════════════════════════════════════════════════════════════════════════


class TestExamDelete:
    def test_delete_exam(self, teacher):
        headers = _auth(teacher)
        # Create an exam
        r = requests.post(
            f"{BASE}/exams",
            json={
                "title": f"Delete-Exam {UNIQUE}",
                "subject": "History",
                "total_questions": 1,
            },
            headers=headers,
            timeout=10,
        )
        assert r.status_code == 201
        exam_id = r.json()["id"]

        # Delete it
        r2 = requests.delete(f"{BASE}/exams/{exam_id}", headers=headers, timeout=10)
        assert r2.status_code == 204

        # Verify deleted
        r3 = requests.get(f"{BASE}/exams/{exam_id}", headers=headers, timeout=10)
        assert r3.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
#  CLEANUP - delete test user's exams at the end (best-effort)
# ═════════════════════════════════════════════════════════════════════════════


def test_cleanup(teacher):
    """Best-effort cleanup of test exams created during this run."""
    headers = _auth(teacher)
    r = requests.get(f"{BASE}/exams", headers=headers, timeout=10)
    if r.status_code == 200:
        for exam in r.json().get("exams", []):
            requests.delete(f"{BASE}/exams/{exam['id']}", headers=headers, timeout=10)
