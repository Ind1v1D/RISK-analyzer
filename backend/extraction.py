"""Step 2 of the analysis pipeline: turn an uploaded file into plain text.

PDF  -> pypdf
DOCX -> python-docx
TXT  -> decoded directly

Anything we can't read raises ExtractionError with a message that is safe to
show the user (FastAPI turns it into a 400 response).
"""

from io import BytesIO

from messages import msg

MIN_TEXT_LENGTH = 50  # below this we assume the upload had no usable text


class ExtractionError(Exception):
    """Raised when usable text cannot be extracted from the upload.

    Carries a message `key` (+ params) instead of a finished sentence so the
    API layer can translate it into the user's language (see messages.py).
    `str(exc)` is the English text, handy for logs.
    """

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        super().__init__(msg(key, "en", **params))


def extract_text(filename: str, content: bytes) -> str:
    """Dispatch on file extension, extract, then clean up the text."""
    ext = ""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[1].lower()

    if ext == "pdf":
        text = _from_pdf(content)
    elif ext == "docx":
        text = _from_docx(content)
    elif ext in ("txt", "text", "md"):
        text = _decode(content)
    else:
        raise ExtractionError("unsupported_type", ext=ext or "?")

    text = _clean(text)
    if len(text) < MIN_TEXT_LENGTH:
        # Almost always a scanned/image-only PDF or an empty document.
        raise ExtractionError("no_text")
    return text


def _from_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            reader.decrypt("")  # try the common empty-password case
        pages = [(page.extract_text() or "") for page in reader.pages]
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("pdf_unreadable", error=exc.__class__.__name__) from exc

    if not pages:
        raise ExtractionError("pdf_no_pages")
    return "\n\n".join(pages)


def _from_docx(content: bytes) -> str:
    from docx import Document

    try:
        doc = Document(BytesIO(content))
    except Exception as exc:
        raise ExtractionError("docx_unreadable", error=exc.__class__.__name__) from exc

    parts: list[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    # Include table cells — fee/payment tables often live in tables.
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _decode(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ExtractionError("bad_encoding")


def _clean(text: str) -> str:
    """Normalize newlines, strip trailing spaces, collapse 3+ blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    blank_run = 0
    for line in text.split("\n"):
        line = line.rstrip()
        if line.strip() == "":
            blank_run += 1
            if blank_run <= 1:  # keep single blank lines as paragraph breaks
                out.append("")
        else:
            blank_run = 0
            out.append(line)
    return "\n".join(out).strip()
