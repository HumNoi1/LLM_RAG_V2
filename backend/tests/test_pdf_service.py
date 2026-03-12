"""
Unit tests for pdf_service — Sprint 2 BE-S.

Tests:
  - parse_pdf: valid PDF file → text extracted
  - parse_pdf: missing file → PDFParseException
  - parse_pdf_bytes: valid PDF bytes → text extracted
  - parse_pdf_bytes: empty bytes → PDFParseException
  - parse_pdf_bytes: invalid bytes → PDFParseException
"""
import io
import os
import tempfile

import pytest

# pdfplumber + fpdf2 for generating test PDFs
from fpdf import FPDF

from app.core.exceptions import PDFParseException
from app.services.pdf_service import parse_pdf, parse_pdf_bytes


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_pdf_bytes(text: str, pages: int = 1) -> bytes:
    """Generate a simple PDF with the given text using fpdf2."""
    pdf = FPDF()
    # Use a built-in font that supports basic latin characters
    pdf.set_auto_page_break(auto=True, margin=15)
    for _ in range(pages):
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, text)
    return pdf.output()


def _make_pdf_file(text: str, pages: int = 1) -> str:
    """Write a test PDF to a temp file and return its path."""
    data = _make_pdf_bytes(text, pages)
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.write(fd, data)
    os.close(fd)
    return path


# ── Tests: parse_pdf (file path) ─────────────────────────────────────────────

class TestParsePdf:
    def test_valid_single_page(self):
        text = "This is a test document for grading."
        path = _make_pdf_file(text)
        try:
            result = parse_pdf(path)
            assert "test document" in result
            assert "grading" in result
        finally:
            os.unlink(path)

    def test_valid_multi_page(self):
        text = "Page content for multi-page test."
        path = _make_pdf_file(text, pages=3)
        try:
            result = parse_pdf(path)
            assert "Page content" in result
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with pytest.raises(PDFParseException, match="File not found"):
            parse_pdf("/nonexistent/path/test.pdf")

    def test_invalid_file(self):
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.write(fd, b"this is not a pdf")
        os.close(fd)
        try:
            with pytest.raises(PDFParseException):
                parse_pdf(path)
        finally:
            os.unlink(path)


# ── Tests: parse_pdf_bytes ────────────────────────────────────────────────────

class TestParsePdfBytes:
    def test_valid_bytes(self):
        text = "Hello from PDF bytes parsing test."
        data = _make_pdf_bytes(text)
        result = parse_pdf_bytes(data, filename="test.pdf")
        assert "PDF bytes parsing" in result

    def test_empty_bytes(self):
        with pytest.raises(PDFParseException, match="Empty file"):
            parse_pdf_bytes(b"", filename="empty.pdf")

    def test_invalid_bytes(self):
        with pytest.raises(PDFParseException):
            parse_pdf_bytes(b"not a pdf", filename="invalid.pdf")

    def test_multi_page_bytes(self):
        text = "Multi-page bytes test content."
        data = _make_pdf_bytes(text, pages=2)
        result = parse_pdf_bytes(data, filename="multi.pdf")
        assert "Multi-page" in result
