"""
PDF Service — parse PDF files to plain text.
BE-S responsibility (Sprint 2).

pdfplumber is the primary parser; handles Thai encoding well.
"""
import io
import logging
from pathlib import Path

import pdfplumber

from app.core.exceptions import PDFParseException

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str | Path) -> str:
    """Extract all text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages.

    Raises:
        PDFParseException: if file cannot be parsed.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise PDFParseException(file_path.name, "File not found")

    try:
        pages_text: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                raise PDFParseException(file_path.name, "PDF has no pages")
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

        full_text = "\n\n".join(pages_text).strip()
        if not full_text:
            raise PDFParseException(file_path.name, "No text could be extracted from PDF")

        logger.info("Parsed PDF '%s': %d pages, %d chars", file_path.name, len(pages_text), len(full_text))
        return full_text

    except PDFParseException:
        raise
    except Exception as e:
        logger.error("Failed to parse PDF '%s': %s", file_path.name, e)
        raise PDFParseException(file_path.name, str(e)) from e


def parse_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> str:
    """Extract text from raw PDF bytes (e.g., from UploadFile).

    Args:
        data: Raw PDF file bytes.
        filename: Original filename (for error messages).

    Returns:
        Concatenated text from all pages.

    Raises:
        PDFParseException: if data cannot be parsed.
    """
    if not data:
        raise PDFParseException(filename, "Empty file")

    try:
        pages_text: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            if len(pdf.pages) == 0:
                raise PDFParseException(filename, "PDF has no pages")
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

        full_text = "\n\n".join(pages_text).strip()
        if not full_text:
            raise PDFParseException(filename, "No text could be extracted from PDF")

        logger.info("Parsed PDF bytes '%s': %d pages, %d chars", filename, len(pages_text), len(full_text))
        return full_text

    except PDFParseException:
        raise
    except Exception as e:
        logger.error("Failed to parse PDF bytes '%s': %s", filename, e)
        raise PDFParseException(filename, str(e)) from e
