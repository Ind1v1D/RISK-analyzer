"""FastAPI app — HTTP entry point for the analysis pipeline.

POST /api/analyze  accepts an uploaded file (PDF/DOCX/TXT) or pasted text and
returns { full_text, summary, flags }. Nothing is stored: the upload lives in
memory for the duration of the request only (MVP constraint — no persistence).
"""

import json
import logging
import os
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from analysis import AnalysisError, analyze_contract
from extraction import ExtractionError, extract_text, prepare_pasted_text
from limits import Busy, RateLimitExceeded, analysis_queue, client_id, rate_limiter
from messages import msg, normalize_lang
from prompts import MAX_FLAGS

logger = logging.getLogger("clausecheck")

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_CHARS = 200_000  # generous single-call limit (~50k tokens)
BODY_OVERHEAD_BYTES = 512 * 1024  # multipart framing + the other form fields

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT_DIR / "samples" / "freelance-agreement.txt"
DIST_DIR = ROOT_DIR / "frontend" / "dist"  # built frontend; served if present

DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()
]


class BodySizeLimitMiddleware:
    """Reject oversized POST /api/analyze bodies before they are buffered.

    Checks Content-Length up front, and also counts bytes of chunked/streamed
    bodies, answering 413 (translated, lang from the query string) as soon as
    the limit is passed.
    """

    def __init__(self, app):
        self.app = app

    @staticmethod
    def limit() -> int:
        return MAX_FILE_BYTES + BODY_OVERHEAD_BYTES

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] != "/api/analyze":
            return await self.app(scope, receive, send)

        limit = self.limit()
        headers = {k.lower(): v for k, v in scope["headers"]}
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = 0
        if declared > limit:
            return await self._reject(scope, send)

        state = {"seen": 0, "rejected": False, "started": False}

        async def counting_receive():
            if state["rejected"]:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                state["seen"] += len(message.get("body", b""))
                if state["seen"] > limit and not state["started"]:
                    state["rejected"] = True
                    await self._reject(scope, send)
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message):
            if state["rejected"]:
                return  # our 413 was already sent; drop whatever the app emits
            if message["type"] == "http.response.start":
                state["started"] = True
            await send(message)

        await self.app(scope, counting_receive, guarded_send)

    @staticmethod
    async def _reject(scope, send):
        query = parse_qs(scope.get("query_string", b"").decode("latin-1"))
        lang = normalize_lang((query.get("lang") or ["en"])[0])
        body = json.dumps({"detail": msg("file_too_large", lang)}).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"connection", b"close"),
            ],
        })
        await send({"type": "http.response.body", "body": body})


app = FastAPI(title="Contract Risk Analysis Assistant", version="0.2.0")

app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)


# `async def` for the trivial endpoints: they run on the event loop and never
# wait for a free worker thread while analyses occupy the thread pool.
@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config")
async def config() -> dict:
    """Public limits, so the UI doesn't have to hard-code them."""
    return {
        "max_file_mb": MAX_FILE_BYTES // (1024 * 1024),
        "max_chars": MAX_CHARS,
        "max_flags": MAX_FLAGS,
    }


@app.get("/api/sample")
def sample(lang: str = "en") -> dict:
    """The demo contract, for the 'See Example Analysis' button."""
    if not SAMPLE_PATH.exists():
        raise HTTPException(404, msg("sample_missing", normalize_lang(lang)))
    return {"text": SAMPLE_PATH.read_text(encoding="utf-8")}


def _check_rate_limit(request: Request, lang: str) -> None:
    try:
        rate_limiter.check(client_id(request))
    except RateLimitExceeded as exc:
        raise HTTPException(
            429,
            msg("rate_limited", lang),
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


# A plain `def` endpoint: FastAPI runs it in a worker thread, so the blocking
# Gemini call and retry sleeps never stall the event loop.
@app.post("/api/analyze")
def analyze(
    request: Request,
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    lang: str = Form(default="en"),  # UI language: en / ru / kk
):
    lang = normalize_lang(lang)

    # --- Step 1: get plain text from either the upload or the paste --------
    # Counting policy (see limits.py): uploads are rate-limited BEFORE parsing
    # because parsing is the expensive part; pasted text is counted only once
    # it has passed validation.
    counted = False
    try:
        if file is not None and file.filename:
            _check_rate_limit(request, lang)
            counted = True
            # Read at most one byte over the limit instead of the whole upload.
            content = file.file.read(MAX_FILE_BYTES + 1)
            if len(content) > MAX_FILE_BYTES:
                raise HTTPException(413, msg("file_too_large", lang))
            full_text = extract_text(file.filename, content)
        elif text and text.strip():
            full_text = prepare_pasted_text(text)
        else:
            raise HTTPException(400, msg("no_input", lang))
    except ExtractionError as exc:
        raise HTTPException(400, msg(exc.key, lang, **exc.params)) from exc

    if len(full_text) > MAX_CHARS:
        raise HTTPException(
            413, msg("too_long", lang, length=len(full_text), limit=MAX_CHARS)
        )

    if not counted:
        _check_rate_limit(request, lang)

    # --- Steps 3-4: LLM call + validation, behind the concurrency queue ----
    try:
        with analysis_queue:
            summary, flags = analyze_contract(full_text, lang)
    except Busy as exc:
        raise HTTPException(
            503, msg("server_busy", lang), headers={"Retry-After": "30"}
        ) from exc
    except AnalysisError as exc:
        headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
        raise HTTPException(exc.status, str(exc), headers=headers) from exc

    # --- Step 5: hand the frontend everything it needs to render ----------
    return {
        "full_text": full_text,
        "summary": summary.model_dump(),
        "flags": [f.model_dump() for f in flags],
    }


# --- Static frontend (single-service deploy) ---------------------------------
# Registered last so /api/* routes always win. Only active when the frontend
# has been built (frontend/dist exists), e.g. inside the Docker image.
if (DIST_DIR / "index.html").is_file():

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str):
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404, "Not found")
        root = DIST_DIR.resolve()
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            headers = None
            if path.startswith("assets/"):
                # Vite fingerprints asset file names, so they can be cached forever.
                headers = {"Cache-Control": "public, max-age=31536000, immutable"}
            return FileResponse(candidate, headers=headers)
        # Missing assets or anything that looks like a file must be a real 404,
        # not index.html (which would break scripts/styles with HTML).
        if path.startswith("assets/") or "." in path.rsplit("/", 1)[-1]:
            raise HTTPException(404, "Not found")
        return FileResponse(root / "index.html")  # SPA fallback
