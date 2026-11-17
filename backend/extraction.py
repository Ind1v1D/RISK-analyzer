"""Step 2 of the analysis pipeline: turn an uploaded file into plain text.

PDF  -> pypdf
DOCX -> python-docx
TXT  -> decoded directly

Anything we can't read raises ExtractionError with a message that is safe to
show the user (FastAPI turns it into a 400 response).
"""

import math
import re
from collections import Counter
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


def prepare_pasted_text(text: str) -> str:
    """Same cleanup + minimum length that uploads get, for pasted text."""
    text = _clean(text)
    if len(text) < MIN_TEXT_LENGTH:
        raise ExtractionError("text_too_short")
    return text


def _from_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            # Try the common empty-password case; 0 == NOT_DECRYPTED.
            if not reader.decrypt(""):
                raise ExtractionError("pdf_encrypted")
        # "plain" mode is the most reliable for contracts; "layout" is only a
        # fallback when plain finds no text at all (some odd encodings).
        pages = [(page.extract_text(extraction_mode="plain") or "") for page in reader.pages]
        if pages and not any(p.strip() for p in pages):
            pages = [(page.extract_text(extraction_mode="layout") or "") for page in reader.pages]
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("pdf_unreadable", error=exc.__class__.__name__) from exc

    if not pages:
        raise ExtractionError("pdf_no_pages")
    return clean_pdf_pages(pages)


# --- PDF layout cleanup (pure functions, unit-tested) -------------------------

_PAGE_NUMBER_RES = (
    re.compile(r"^(page|p\.|стр\.?|страница|бет)\s*\d+(\s*(of|из|/|от)\s*\d+)?$", re.I),
    re.compile(r"^[-–—]\s*\d+\s*[-–—]$"),
    re.compile(r"^\d+\s*(/|of|из)\s*\d+$", re.I),
)
_LONE_NUMBER_RE = re.compile(r"^\d{1,4}$")
_HYPHEN_BREAK_RE = re.compile(r"(?<=[^\W\d_])-\n(?=[^\W\d_])")
# Lines that start a new structural element: "1.", "2.1", "(a)", "a)", bullets.
_STRUCTURAL_RE = re.compile(
    r"^(\d+(\.\d+)*[.)]?\s|\(?[a-zA-Zа-яА-Я]\)\s|\((\d+|[ivxIVX]+)\)\s|[-•*–·▪●■]\s)"
)
_NUMBERED_RE = re.compile(r"^\d+(\.\d+)*[.)]?\s")
_HEADING_WORD_RE = re.compile(
    r"^(article|section|clause|schedule|appendix|annex|раздел|статья|глава|пункт|приложение)\b",
    re.I,
)
_TERMINAL = ".!?:;"
_EDGE_LINES = 3  # lines at the top/bottom of a page considered for page numbers
_RUNNING_LINES = 2  # lines at the top/bottom considered running header/footer


def is_page_number_line(line: str, *, allow_lone_number: bool = True) -> bool:
    """'Page 3 of 10', '- 3 -', '3 / 10' and (optionally) a lone '3'."""
    text = line.strip()
    if not text:
        return False
    if any(r.match(text) for r in _PAGE_NUMBER_RES):
        return True
    return allow_lone_number and bool(_LONE_NUMBER_RE.match(text))


def join_hyphenated(text: str) -> str:
    """Join words split by a line-end hyphen ("termi-" / "nation" -> "termination").

    Only when the next line continues in lowercase, so "- item" bullets and
    "Smith-" / "Jones" style names are left alone.
    """
    out = []
    pos = 0
    for m in _HYPHEN_BREAK_RE.finditer(text):
        if text[m.end()].islower():
            out.append(text[pos:m.start()])
            pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def _page_lines(page_text: str) -> list[str]:
    text = page_text.replace("\r\n", "\n").replace("\r", "\n")
    return [re.sub(r"[ \t]+", " ", raw).strip() for raw in text.split("\n")]


def strip_page_numbers(lines: list[str]) -> list[str]:
    """Drop page-number lines of one page.

    Explicit forms ('Page 3 of 10', '- 3 -') are removed anywhere; a bare
    number only when it is among the first/last non-empty lines of the page,
    so numbers inside tables or text are left alone.
    """
    idx = [i for i, line in enumerate(lines) if line]
    edge = set(idx[:_EDGE_LINES]) | set(idx[-_EDGE_LINES:])
    return [
        line for i, line in enumerate(lines)
        if not is_page_number_line(line, allow_lone_number=i in edge)
    ]


_EDGE_NUMBER_RE = re.compile(r"^\W*\d+\W*|\W*\d+\W*$")


def _shape(line: str) -> str:
    """Key for comparing header/footer lines across pages.

    Case/spacing-insensitive, and a page number at the very start or end of
    the line is ignored ("Contract v1 - 3" matches "Contract v1 - 4"); digits
    in the middle of a line are kept so numbered body text never matches.
    """
    return _EDGE_NUMBER_RE.sub("", " ".join(line.lower().split())).strip()


def remove_repeated_edges(pages: list[list[str]]) -> list[list[str]]:
    """Remove running headers/footers: edge lines repeated on most pages.

    Needs >= 3 pages. A line counts when its digit-insensitive shape appears
    within the top/bottom two lines of at least max(3, 60% of pages) pages.
    Only edge positions are cleaned, so body text that merely repeats stays.
    """
    if len(pages) < 3:
        return pages

    def edge_indexes(lines: list[str]) -> list[int]:
        idx = [i for i, line in enumerate(lines) if line]
        return sorted(set(idx[:_RUNNING_LINES] + idx[-_RUNNING_LINES:]))

    counts: Counter = Counter()
    for lines in pages:
        for shape in {_shape(lines[i]) for i in edge_indexes(lines)}:
            counts[shape] += 1

    threshold = max(3, math.ceil(0.6 * len(pages)))
    repeated = {s for s, c in counts.items() if c >= threshold and s}
    result = []
    for lines in pages:
        drop = {i for i in edge_indexes(lines) if _shape(lines[i]) in repeated}
        result.append([line for i, line in enumerate(lines) if i not in drop])
    return result


def _is_heading(line: str) -> bool:
    if _HEADING_WORD_RE.match(line) and len(line) <= 80 and line[-1] not in _TERMINAL:
        return True
    letters = [c for c in line if c.isalpha()]
    return bool(letters) and line.upper() == line and len(line) <= 80 and line[-1] not in ",;"


def rejoin_lines(lines: list[str]) -> str:
    """Merge lines wrapped mid-sentence into paragraphs.

    Kept on their own lines: blank-line paragraph breaks, numbered clauses
    ('1.', '2.1', '(a)'), bullets, headings, and any line after a sentence end.
    """
    out: list[str] = []
    prev = ""  # the paragraph line being built ("" => nothing pending)
    for line in lines:
        if not line:
            if prev:
                out.append(prev)
                prev = ""
            if out and out[-1] != "":
                out.append("")
            continue
        if not prev:
            prev = line
            continue

        starts_new = bool(_STRUCTURAL_RE.match(line)) or _is_heading(line)
        prev_done = (
            prev[-1] in _TERMINAL
            or _is_heading(prev)
            # short numbered title such as "3. Payment" followed by body text
            or (bool(_NUMBERED_RE.match(prev)) and len(prev) <= 50 and line[0].isupper())
        )
        if starts_new or prev_done:
            out.append(prev)
            prev = line
        else:
            prev = prev + " " + line
    if prev:
        out.append(prev)
    return "\n".join(out)


def clean_pdf_pages(page_texts: list[str]) -> str:
    """Full PDF cleanup pipeline over per-page extracted text."""
    pages = [_page_lines(join_hyphenated("\n".join(_page_lines(t)))) for t in page_texts]
    pages = [strip_page_numbers(p) for p in pages]
    pages = remove_repeated_edges(pages)
    # One continuous stream so sentences wrapped across a page break rejoin.
    flat: list[str] = []
    for p in pages:
        flat.extend(p)
    return rejoin_lines(flat)


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
