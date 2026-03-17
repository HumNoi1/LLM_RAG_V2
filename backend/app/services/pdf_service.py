"""
PDF Service — parse PDF files to plain text.
BE-S responsibility (Sprint 2).

pdfplumber is the primary parser; handles Thai encoding well.
"""
import io
from pathlib import Path

import pdfplumber

from app.core.exceptions import PDFParseException


def parse_pdf(file_path: str | Path) -> str:
    """Extract all text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages, with pages separated by newlines.

    Raises:
        PDFParseException: if file cannot be parsed.
    """
    filename = str(file_path)
    try:
        with pdfplumber.open(file_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())
            return "\n\n".join(pages_text)
    except Exception as exc:
        raise PDFParseException(filename, reason=str(exc)) from exc


def parse_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> str:
    """Extract text from raw PDF bytes (e.g., from UploadFile).

    Args:
        data:     Raw PDF bytes.
        filename: Original filename for error messages.

    Returns:
        Concatenated text from all pages.

    Raises:
        PDFParseException: if file cannot be parsed.
    """
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())
            return "\n\n".join(pages_text)
    except Exception as exc:
        raise PDFParseException(filename, reason=str(exc)) from exc
