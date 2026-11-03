"""Step 3 of the analysis pipeline: the prompt + structured output schema.

Gemini is told to fill the AnalysisResult schema below, so its reply is always
parseable JSON rather than free-form text. Keep this file separate from the
pipeline code so non-engineers on the team can tune the wording safely.
"""

from typing import Literal

from pydantic import BaseModel, Field

from messages import LANGUAGE_NAMES, normalize_lang


class ClauseFlag(BaseModel):
    """One risky/unclear clause the model found in the contract."""

    clause_text: str = Field(
        description=(
            "VERBATIM excerpt copied character-for-character from the contract, "
            "including original punctuation and capitalization. Never paraphrase."
        )
    )
    risk_level: Literal["High", "Medium", "Low"]
    explanation: str = Field(
        description="Plain-language, hedged explanation of why the clause was flagged."
    )


class AnalysisResult(BaseModel):
    """Top-level shape Gemini must return. An empty `flags` list = clean contract."""

    flags: list[ClauseFlag]


SYSTEM_PROMPT = """\
You are a first-pass contract review assistant for non-lawyers. You spot clauses
with a plausible legal or practical concern and explain them in plain language.

Rules:
1. Only flag clauses with a plausible, specific concern: one-sided terms,
   unusual obligations, vague language with real consequences, hidden fees or
   penalties, broad liability, or easy-to-miss deadlines. Do NOT flag ordinary
   boilerplate just because it is dense or legalistic. If the contract looks
   fine, return an empty list — a clean result is a valid answer.
2. "clause_text" must be an EXACT verbatim substring of the provided contract,
   copied character-for-character (same punctuation, capitalization, and
   wording). Do not paraphrase, summarize, "fix" the text, or normalize
   whitespace inside the excerpt. Keep each excerpt short — usually one to
   three sentences — and self-contained so it can be located and highlighted.
3. "risk_level":
   - "High": could cause serious financial, legal, or practical harm.
   - "Medium": a meaningful but bounded concern worth understanding before signing.
   - "Low": minor wording or ambiguity worth a second look.
4. "explanation": plain, non-legal language a non-lawyer can understand, in 1-3
   sentences. Say what the clause does and why it may be unfavorable or unclear,
   and hedge appropriately — e.g. "this may be worth reviewing with a lawyer
   because...". Never claim certainty about legal outcomes, never cite statutes
   by name, and never tell the user what to decide.
5. Return at most 12 flags, most significant first. Skip marginal issues rather
   than padding the list.
"""


def build_system_prompt(lang: str = "en") -> str:
    """SYSTEM_PROMPT plus the output-language rule for the user's UI language.

    Only the "explanation" text is translated. "clause_text" must stay a
    verbatim excerpt in the contract's own language, or highlighting breaks.
    """
    language = LANGUAGE_NAMES[normalize_lang(lang)]
    return (
        SYSTEM_PROMPT
        + f"""\
6. Write every "explanation" in {language}, using natural, everyday {language}
   (including the hedging, e.g. "this may be worth reviewing with a lawyer").
   Keep "clause_text" EXACTLY as it appears in the contract, in the contract's
   original language — never translate it, whatever language the contract is in.
"""
    )
