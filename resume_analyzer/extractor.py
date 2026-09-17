"""
PDF text extraction (Milestone 5).

Uses PyMuPDF (imported as `fitz`) to read text from an uploaded resume.
Nothing here does NLP, scoring or matching - it only turns a PDF into a
plain text string plus a little metadata, and reports problems clearly.

The uploaded file is opened read-only; it is never modified or rewritten.
"""

import re
from typing import Optional

import fitz  # PyMuPDF


class ExtractionError(Exception):
    """Raised when a PDF cannot be read or contains no readable text.

    The message is always safe to show to the user (no tracebacks, no
    file system paths).
    """


# Minimum number of characters before we consider a PDF "readable".
MIN_USEFUL_CHARS = 20


def clean_text(raw_text: str) -> str:
    """Tidy the extracted text without changing its wording.

    - trailing spaces on each line are removed
    - runs of blank lines collapse into a single blank line
    - meaningful line breaks are preserved (no re-flowing of sentences)
    """
    lines = [line.rstrip() for line in raw_text.replace("\r\n", "\n").split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(file_path: str) -> dict:
    """Extract text from every page of the PDF at `file_path`.

    Returns a dict: {"text": str, "page_count": int, "char_count": int}
    Raises ExtractionError with a user-friendly message on any problem.
    """
    document: Optional[fitz.Document] = None
    try:
        try:
            document = fitz.open(file_path)
        except Exception:
            # Covers missing, damaged and non-PDF-content files.
            raise ExtractionError(
                "This PDF could not be opened. It may be corrupted or incomplete."
            )

        if document.needs_pass:
            raise ExtractionError(
                "This PDF is password protected, so its text cannot be read. "
                "Please upload an unprotected version."
            )

        page_count = document.page_count
        if page_count == 0:
            raise ExtractionError("This PDF has no pages.")

        pages = []
        for page in document:
            try:
                pages.append(page.get_text("text") or "")
            except Exception:
                # One unreadable page should not fail the whole resume.
                pages.append("")

        # A blank line between pages keeps paragraphs readable.
        text = clean_text("\n\n".join(pages))

        if len(text) < MIN_USEFUL_CHARS:
            raise ExtractionError(
                "No readable text could be extracted from this PDF. "
                "It may be a scanned or image-only document."
            )

        return {"text": text, "page_count": page_count, "char_count": len(text)}

    except ExtractionError:
        raise
    except Exception:
        # Anything unexpected becomes a friendly message, never a traceback.
        raise ExtractionError(
            "An unexpected error occurred while reading this PDF. Please try again."
        )
    finally:
        if document is not None:
            try:
                document.close()
            except Exception:
                pass


def preview(text: str, limit: int = 600) -> str:
    """A short, unmodified beginning of the extracted text for display."""
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."
