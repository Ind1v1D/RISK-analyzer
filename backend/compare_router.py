"""API routes for comparing two versions of a contract."""

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from contract_compare import compare_contracts
from extraction import ExtractionError, extract_text

router = APIRouter()
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_CHARS = 200_000
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class CompareRequest(BaseModel):
    v1: str
    v2: str


def _compare(v1: str, v2: str):
    if not v1.strip() or not v2.strip():
        raise HTTPException(422, "Both contract versions are required.")
    if len(v1) > MAX_CHARS or len(v2) > MAX_CHARS:
        raise HTTPException(413, "Each version must be under 200,000 characters.")
    try:
        return compare_contracts(v1, v2)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/api/compare")
def compare_text(request: CompareRequest):
    """Compare two pasted contract versions."""
    return _compare(request.v1, request.v2)


async def _read_version(file: UploadFile) -> str:
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, f"{filename or 'File'}: only PDF, DOCX, TXT, and MD are accepted.")
    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(413, f"{filename} is larger than 10 MB.")
    try:
        extracted = extract_text(filename, content)
    except ExtractionError as exc:
        raise HTTPException(400, str(exc)) from exc
    if len(extracted) > MAX_CHARS:
        raise HTTPException(413, f"{filename} is over 200,000 characters.")
    return extracted


@router.post("/api/compare/files")
async def compare_files(v1: UploadFile = File(...), v2: UploadFile = File(...)):
    """Compare two uploaded files. Both uploads are read and discarded in memory."""
    first, second = await _read_version(v1), await _read_version(v2)
    return _compare(first, second)
