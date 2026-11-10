"""Steps 3-4 of the analysis pipeline: call Gemini, validate structured output.

Flow:
  contract text -> Gemini (JSON-schema-constrained) -> AnalysisResult (Pydantic)
  -> deduped, capped list of ClauseFlag objects for the frontend.

Resilience: transient errors (503 demand spikes, 429 rate limits) are retried
with exponential backoff; if the primary model stays unavailable we discover
another text model this API key can use and fall back to it once.
"""

import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError

from messages import msg
from prompts import AnalysisResult, ClauseFlag, build_system_prompt

load_dotenv()  # reads backend/.env into the environment

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_FLAGS = 20      # hard cap regardless of what the model returns
# IMP-2 (stable results): the same contract must give the same risk levels, so
# sampling randomness is removed (temperature 0 + fixed seed) and the output
# order is deterministic (see _postprocess).
TEMPERATURE = 0.0
SEED = int(os.getenv("GEMINI_SEED", "42"))
RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2}
MAX_ATTEMPTS = 4    # tries per model for transient errors (2s, 4s, 8s backoff)

# Temporary problems — worth retrying the same model.
TRANSIENT_MARKERS = (
    "503", "429", "500",
    "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED",
)
# Problems where switching models may help (retired/renamed model = 404).
FALLBACK_MARKERS = TRANSIENT_MARKERS + ("404", "NOT_FOUND")


class AnalysisError(Exception):
    """Raised when the LLM call or its output can't be used; message is user-safe.

    Built from a message `key` so it is already in the user's language.
    """


def analyze_contract(full_text: str, lang: str = "en") -> list[ClauseFlag]:
    """Return validated clause flags; explanations/errors are in `lang` (en/ru/kk)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AnalysisError(msg("missing_api_key", lang))

    client = genai.Client(api_key=api_key)

    response, last_exc = _generate(client, MODEL, full_text, lang)

    # Primary model still unavailable? Try one fallback model (e.g. a -lite
    # variant under lighter demand) before giving up.
    if response is None and last_exc is not None and _matches(last_exc, FALLBACK_MARKERS):
        fallback = _pick_fallback_model(client)
        if fallback:
            print(f"[analysis] {MODEL} unavailable; retrying with fallback: {fallback}", flush=True)
            response, last_exc = _generate(client, fallback, full_text, lang)

    if response is None:
        exc = last_exc
        detail = str(exc).strip().replace("\n", " ")[:300]
        error = exc.__class__.__name__
        message = (
            msg("ai_failed_detail", lang, error=error, detail=detail)
            if detail
            else msg("ai_failed", lang, error=error)
        )
        raise AnalysisError(message) from exc

    result = _parse(response, lang)
    return _postprocess(result.flags, full_text)


def _matches(exc: Exception, markers: tuple[str, ...]) -> bool:
    """Heuristic: does the error text indicate one of our known conditions?"""
    message = str(exc)
    return any(marker in message for marker in markers)


def _generate(client, model: str, full_text: str, lang: str = "en"):
    """Call Gemini once per attempt; returns (response | None, error | None).

    Retries only transient errors — auth failures and bad requests fail fast.
    """
    last_exc: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
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
                ),
            )
            return response, None
        except Exception as exc:
            last_exc = exc
            if not _matches(exc, TRANSIENT_MARKERS):
                return None, exc  # permanent error — don't waste retries
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 ** (attempt + 1))  # 2s, 4s, 8s
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

    names = []
    for entry in entries:
        name = (getattr(entry, "name", "") or "").removeprefix("models/")
        actions = getattr(entry, "supported_actions", None)
        if actions and "generateContent" not in actions:
            continue  # skip embeddings/image/etc. when metadata is available
        if name and name != MODEL:
            names.append(name)

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
