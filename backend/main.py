"""FastAPI app — HTTP entry point for the analysis pipeline.

POST /api/analyze  accepts an uploaded file (PDF/DOCX/TXT) or pasted text and
returns { full_text, flags }. Nothing is stored: the upload lives in memory
for the duration of the request only (MVP constraint — no persistence).
"""

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from analysis import AnalysisError, analyze_contract
from extraction import ExtractionError, extract_text
from messages import msg, normalize_lang
from compare_router import router as compare_router

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_CHARS = 200_000  # generous single-call limit (~50k tokens)

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "samples" / "freelance-agreement.txt"

app = FastAPI(title="Contract Risk Analysis Assistant", version="0.1.0")
app.include_router(compare_router)

# Vite dev server origin; harmless if it never matches (the dev proxy is primary).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/sample")
def sample(lang: str = "en") -> dict:
    """The demo contract, for the 'See Example Analysis' button."""
    if not SAMPLE_PATH.exists():
        raise HTTPException(404, msg("sample_missing", normalize_lang(lang)))
    return {"text": SAMPLE_PATH.read_text(encoding="utf-8")}


@app.post("/api/analyze")
async def analyze(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    lang: str = Form(default="en"),  # UI language: en / ru / kk
):
    lang = normalize_lang(lang)

    # --- Step 1: get plain text from either the upload or the paste --------
    if file is not None and file.filename:
        content = await file.read()
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(413, msg("file_too_large", lang))
        try:
            full_text = extract_text(file.filename, content)
        except ExtractionError as exc:
            raise HTTPException(400, msg(exc.key, lang, **exc.params)) from exc
    elif text and text.strip():
        full_text = text.strip()
    else:
        raise HTTPException(400, msg("no_input", lang))

    if len(full_text) > MAX_CHARS:
        raise HTTPException(
            413, msg("too_long", lang, length=len(full_text), limit=MAX_CHARS)
        )

    # --- Steps 3-4: LLM call + validation (see analysis.py) ---------------
    try:
        flags = analyze_contract(full_text, lang)
    except AnalysisError as exc:
        raise HTTPException(502, str(exc)) from exc

    # --- Step 5: hand the frontend everything it needs to render ----------
    return {"full_text": full_text, "flags": [f.model_dump() for f in flags]}
