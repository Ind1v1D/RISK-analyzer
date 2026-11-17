"""Steps 3-4 of the analysis pipeline: call Gemini, validate structured output.

Flow:
  contract text -> Gemini (JSON-schema-constrained) -> AnalysisResult (Pydantic)
  -> deduped, capped list of ClauseFlag objects for the frontend.

Resilience: transient errors (503 demand spikes, 429 rate limits) are retried
with exponential backoff; if the primary model stays unavailable we discover
another text model this API key can use and fall back to it once.
"""

import json
import logging
import os
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from messages import msg
from prompts import MAX_FLAGS, AnalysisResult, ClauseFlag, ContractSummary, build_system_prompt

load_dotenv()  # reads backend/.env into the environment

logger = logging.getLogger("clausecheck.analysis")

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_KEY_TERMS = 6
# IMP-2 (stable results): the same contract must give the same risk levels, so
# sampling randomness is removed (temperature 0 + fixed seed) and the output
# order is deterministic (see _postprocess).
TEMPERATURE = 0.0
SEED = int(os.getenv("GEMINI_SEED", "42"))
RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2}
MAX_ATTEMPTS = 4    # tries per model for transient errors (2s, 4s, 8s backoff)
# Time budget. The frontend gives up after 150 s; queue wait (<= QUEUE_TIMEOUT,
# 30 s default) + this deadline must stay below that.
GEMINI_TIMEOUT_SECONDS = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60"))  # one HTTP call
ANALYSIS_DEADLINE_SECONDS = float(os.getenv("ANALYSIS_DEADLINE_SECONDS", "110"))  # all attempts
MIN_ATTEMPT_SECONDS = 10  # don't start a call that can't plausibly finish
QUOTA_RETRY_AFTER = 60  # seconds suggested to the client when Gemini quota is out

# HTTP status codes from the Gemini API.
QUOTA_CODES = {429}
TRANSIENT_CODES = {408, 429, 500, 502, 503, 504}
FALLBACK_CODES = TRANSIENT_CODES | {404}
# Fallback only for errors that are NOT APIError (network/timeouts), where no
# structured status exists.
_NETWORK_MARKERS = ("UNAVAILABLE", "DEADLINE_EXCEEDED", "timed out", "timeout", "connection")

# Model-name fragments we never pick as an automatic fallback.
_UNSTABLE_FRAGMENTS = ("preview", "exp", "tts", "image", "live", "embedding")


class AnalysisError(Exception):
    """Raised when the LLM call or its output can't be used; message is user-safe.

    Already translated. `status` is the HTTP status the API should answer with
    (502 AI failure, 429 AI quota); `retry_after` (seconds) is sent as a header.
    """

    def __init__(self, message: str, status: int = 502, retry_after: int | None = None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


def analyze_contract(full_text: str, lang: str = "en") -> tuple[ContractSummary, list[ClauseFlag]]:
    """Return (summary, validated flags); texts/errors are in `lang` (en/ru/kk)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not set: add it to backend/.env or the host's environment")
        raise AnalysisError(msg("missing_api_key", lang), status=503)

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=int(GEMINI_TIMEOUT_SECONDS * 1000)),  # ms
    )
    deadline = time.monotonic() + ANALYSIS_DEADLINE_SECONDS

    response, last_exc = _generate(client, MODEL, full_text, lang, deadline)

    # Primary model still unavailable? Try one fallback model (e.g. a -lite
    # variant under lighter demand) before giving up.
    if response is None and last_exc is not None and _is_fallback_worthy(last_exc):
        fallback = _pick_fallback_model(client)
        if fallback:
            logger.warning("%s unavailable; retrying with fallback: %s", MODEL, fallback)
            response, last_exc = _generate(client, fallback, full_text, lang, deadline)

    if response is None:
        # Details go to the server log only; users get a generic translated text.
        logger.error("Gemini request failed: %s: %s", last_exc.__class__.__name__, last_exc)
        if last_exc is not None and _is_quota(last_exc):
            raise AnalysisError(
                msg("ai_quota", lang), status=429, retry_after=QUOTA_RETRY_AFTER
            ) from last_exc
        raise AnalysisError(msg("ai_failed", lang), status=502) from last_exc

    result = _parse(response, lang)
    return _clean_summary(result.summary), _postprocess(result.flags, full_text)


def _status_code(exc: Exception) -> int | None:
    """Structured HTTP status of a Gemini SDK error, if it has one."""
    if isinstance(exc, genai_errors.APIError):
        code = getattr(exc, "code", None)
        return code if isinstance(code, int) else None
    return None


def _is_quota(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.APIError):
        return _status_code(exc) in QUOTA_CODES or getattr(exc, "status", None) == "RESOURCE_EXHAUSTED"
    return False


def _is_transient(exc: Exception) -> bool:
    """Temporary problem worth retrying the same model."""
    if isinstance(exc, genai_errors.APIError):
        return _status_code(exc) in TRANSIENT_CODES or getattr(exc, "status", None) in (
            "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED", "INTERNAL",
        )
    # Not an SDK error: network/timeout failures. Structured types first,
    # then a conservative text fallback.
    if isinstance(exc, (httpx.TransportError, TimeoutError, ConnectionError)):
        return True
    text = str(exc)
    return any(marker.lower() in text.lower() for marker in _NETWORK_MARKERS)


def _is_fallback_worthy(exc: Exception) -> bool:
    """Switching model may help: transient, or the model is gone (404)."""
    if isinstance(exc, genai_errors.APIError):
        return _status_code(exc) in FALLBACK_CODES or _is_transient(exc) or (
            getattr(exc, "status", None) == "NOT_FOUND"
        )
    return _is_transient(exc)


def _generate(client, model: str, full_text: str, lang: str = "en", deadline: float | None = None):
    """Call Gemini once per attempt; returns (response | None, error | None).

    Retries only transient errors (2s/4s/8s backoff) and stops when `deadline`
    (time.monotonic value) leaves no room for another attempt. Quota errors
    (429) are NOT retried here: they return at once so the caller can try the
    fallback model a single time and then report "quota reached".
    """
    last_exc: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining < MIN_ATTEMPT_SECONDS:
            break
        call_timeout = GEMINI_TIMEOUT_SECONDS
        if remaining is not None:
            call_timeout = min(call_timeout, remaining)
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"Review this contract:\n\n{full_text}",
                config=types.GenerateContentConfig(
                    system_instruction=build_system_prompt(lang),
                    # Constrain output to our schema so parsing never depends
                    # on the model cooperating with free-form instructions.
                    response_mime_type="application/json",
                    response_schema=AnalysisResult,
                    temperature=TEMPERATURE,
                    seed=SEED,
                    http_options=types.HttpOptions(timeout=int(call_timeout * 1000)),
                ),
            )
            return response, None
        except Exception as exc:
            last_exc = exc
            if _is_quota(exc):
                return None, exc  # quota: no backoff retries on the same model
            if not _is_transient(exc):
                return None, exc  # permanent error — don't waste retries
            if attempt < MAX_ATTEMPTS - 1:
                delay = 2 ** (attempt + 1)
                if deadline is not None and deadline - time.monotonic() < delay + MIN_ATTEMPT_SECONDS:
                    break  # next attempt would not fit in the budget
                time.sleep(delay)
    return None, last_exc


def _pick_fallback_model(client) -> str | None:
    """Discover another text model this API key can use.

    Preference order: a 'lite' variant of the same version (lighter demand),
    then any other flash-class model.
    """
    try:
        entries = list(client.models.list())
    except Exception:
        return None

    names = set()
    for entry in entries:
        name = (getattr(entry, "name", "") or "").removeprefix("models/")
        actions = getattr(entry, "supported_actions", None)
        if actions and "generateContent" not in actions:
            continue  # skip embeddings/image/etc. when metadata is available
        if not name or name == MODEL:
            continue
        if any(fragment in name.lower() for fragment in _UNSTABLE_FRAGMENTS):
            continue  # never fall back to preview/experimental/special models
        names.add(name)
    names = sorted(names)  # deterministic order

    version = MODEL[: MODEL.find("-flash")] if "-flash" in MODEL else "gemini"
    same_version = [n for n in names if n.startswith(version)]

    lite = [n for n in same_version if "lite" in n] or [n for n in names if "lite" in n]
    if lite:
        return lite[0]
    flash = [n for n in same_version if "flash" in n] or [n for n in names if "flash" in n]
    if flash:
        return flash[0]
    return None


def _parse(response, lang: str = "en") -> AnalysisResult:
    """Use the SDK's parsed object when available, else validate raw JSON."""
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, AnalysisResult):
        return parsed

    raw = getattr(response, "text", None)
    if not raw:
        raise AnalysisError(msg("ai_empty", lang))
    try:
        return AnalysisResult.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise AnalysisError(msg("ai_unreadable", lang)) from exc


def _norm(text: str) -> str:
    """Whitespace/case-insensitive form used for matching excerpts."""
    return " ".join(text.split()).lower()


def _postprocess(flags: list[ClauseFlag], full_text: str = "") -> list[ClauseFlag]:
    """Drop duplicates / empty excerpts, order deterministically, then cap.

    - Duplicates (same excerpt ignoring case/spacing): keep the most serious one;
      ties are broken by the text itself, never by the order the model listed them.
    - Order = High, Medium, Low; within a level, by position in the contract.
    - The cap keeps the most serious flags rather than the first ones listed.
    So the same set of model findings always produces the same result.
    """
    def severity(flag: ClauseFlag) -> int:
        return RISK_ORDER.get(flag.risk_level, len(RISK_ORDER))

    best: dict[str, ClauseFlag] = {}
    for flag in flags:
        excerpt = _norm(flag.clause_text)
        if not excerpt:
            continue
        rank = (severity(flag), flag.clause_text, flag.explanation)
        current = best.get(excerpt)
        if current is None or rank < (severity(current), current.clause_text, current.explanation):
            best[excerpt] = flag

    haystack = _norm(full_text)

    def sort_key(item: tuple[str, ClauseFlag]):
        excerpt, flag = item
        position = haystack.find(excerpt)
        return (
            severity(flag),
            position if position >= 0 else len(haystack),  # unmatched excerpts last
            excerpt,
        )

    ordered = [flag for _, flag in sorted(best.items(), key=sort_key)]
    return ordered[:MAX_FLAGS]


def _clean_summary(summary: ContractSummary) -> ContractSummary:
    """Trim whitespace, drop empty entries, cap key_terms."""
    return ContractSummary(
        contract_type=summary.contract_type.strip(),
        parties=[p.strip() for p in summary.parties if p.strip()],
        overview=summary.overview.strip(),
        key_terms=[t.strip() for t in summary.key_terms if t.strip()][:MAX_KEY_TERMS],
    )
