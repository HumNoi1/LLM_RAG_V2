"""
PDF Service — parse PDF files to plain text.
BE-S responsibility (Sprint 2).

pdfplumber is the primary parser; handles Thai encoding well.
"""
from pathlib import Path
from typing import Optional

import pdfplumber


def parse_pdf(file_path: str | Path) -> str:
    """Extract all text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages.

    Raises:
        PDFParseException: if file cannot be parsed.
    """
    # Sprint 2 implementation
    raise NotImplementedError("pdf_service.parse_pdf — implement in Sprint 2")


def parse_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> str:
    """Extract text from raw PDF bytes (e.g., from UploadFile).

    Sprint 2 implementation.
    """
    raise NotImplementedError("pdf_service.parse_pdf_bytes — implement in Sprint 2")
