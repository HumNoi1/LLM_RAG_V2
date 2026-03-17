"""
Tests for app.services.pdf_service

Covers:
  - parse_pdf_bytes() with a valid PDF → returns non-empty string
  - parse_pdf_bytes() with empty bytes → raises PDFParseException
  - parse_pdf_bytes() with garbage bytes → raises PDFParseException
  - parse_pdf() with a temp file → returns non-empty string
"""

import io
import tempfile
from pathlib import Path

import pytest
from fpdf import FPDF

from app.core.exceptions import PDFParseException
from app.services.pdf_service import parse_pdf, parse_pdf_bytes


# ── Helper ────────────────────────────────────────────────────────────────────


def _make_pdf(text: str = "Hello World") -> bytes:
    """Generate a minimal PDF containing the given text."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt=text, ln=True)
    return bytes(pdf.output())


# ── parse_pdf_bytes ───────────────────────────────────────────────────────────


class TestParsePdfBytes:
    def test_valid_pdf_returns_text(self):
        data = _make_pdf("Exam Answer Key Question 1")
        result = parse_pdf_bytes(data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_valid_pdf_contains_expected_content(self):
        data = _make_pdf("UniqueMarker12345")
        result = parse_pdf_bytes(data)
        assert "UniqueMarker12345" in result

    def test_empty_bytes_raises_exception(self):
        with pytest.raises(PDFParseException):
            parse_pdf_bytes(b"")

    def test_garbage_bytes_raises_exception(self):
        with pytest.raises(PDFParseException):
            parse_pdf_bytes(b"\x00\x01\x02\x03 not a pdf at all !!!")

    def test_custom_filename_in_exception(self):
        try:
            parse_pdf_bytes(b"garbage", filename="my_exam.pdf")
            pytest.fail("Expected PDFParseException")
        except PDFParseException as exc:
            assert "my_exam.pdf" in str(exc)

    def test_multipage_pdf(self):
        pdf = FPDF()
        for i in range(3):
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            pdf.cell(200, 10, txt=f"Page {i + 1} content", ln=True)
        data = bytes(pdf.output())
        result = parse_pdf_bytes(data)
        # All three pages should be represented
        assert "Page 1" in result
        assert "Page 2" in result
        assert "Page 3" in result


# ── parse_pdf (file path) ─────────────────────────────────────────────────────


class TestParsePdf:
    def test_valid_pdf_file_returns_text(self, tmp_path: Path):
        data = _make_pdf("Answer Key Content")
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(data)

        result = parse_pdf(pdf_file)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_nonexistent_file_raises_exception(self):
        with pytest.raises(PDFParseException):
            parse_pdf("/nonexistent/path/does_not_exist.pdf")

    def test_path_object_accepted(self, tmp_path: Path):
        data = _make_pdf("PathObject test")
        pdf_file = tmp_path / "path_test.pdf"
        pdf_file.write_bytes(data)

        result = parse_pdf(pdf_file)
        assert "PathObject" in result
