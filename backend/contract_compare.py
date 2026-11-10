"""Rule-based comparison of two contract versions.

The comparison is intentionally deterministic and keeps the original text in
the response. It highlights changed clauses and common commercial terms; it is
not a legal opinion.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher


DISCLAIMER = "AI-generated starting points — not legal advice."
_NUMBERED = re.compile(r"^\s*(\d+(?:\.\d+)*\.?)[)\s]+(.*)$")
_AMOUNTS = re.compile(
    r"(?i)(?:\b\d[\d,]*(?:\.\d+)?\s*(?:%|percent|days?|years?|months?)"
    r"|\$\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s*(?:kzt|usd|eur)\b)"
)
_HIGH = (
    re.compile(r"\bnon[- ]compete\b", re.I),
    re.compile(r"waiv(?:e|es|er).*\bfees?\b", re.I),
    re.compile(r"unlimited\s+(?:liability|damages|claims)", re.I),
    re.compile(r"sole\s+and\s+absolute\s+discretion", re.I),
    re.compile(r"indemnif(?:y|ication).*unlimited", re.I),
)
_MEDIUM = (
    re.compile(r"\b(?:ninety|sixty|forty[- ]five)\s*\(?(?:\d+)?\)?\s*days?\b|\b(?:60|90|120)\s+days?\b", re.I),
    re.compile(r"\bwithout\s+limitation\b|\bunlimited\s+(?:number|scope|revisions)\b", re.I),
    re.compile(r"\bautomatic(?:ally)?\s+renew", re.I),
    re.compile(r"\bterminate\b.{0,60}\bany\s+time\b", re.I),
    re.compile(r"\bno\s+liability\s+cap\b", re.I),
)
_LOW = (
    re.compile(r"\bcommercially\s+reasonable\b|\breasonable\s+efforts\b", re.I),
    re.compile(r"\bpromptly\b|\bin a timely manner\b", re.I),
)
_PROTECTIVE = re.compile(
    r"\b(?:liability\s+)?cap\b|\blimit(?:ation)?\s+of\s+liability\b|"
    r"\bliability\s+shall\s+not\s+exceed\b|\bmaximum\s+liability\b",
    re.I,
)


def _normal(text: str) -> str:
    return " ".join(text.split()).casefold()


def _body_signature(text: str) -> str:
    text = _NUMBERED.sub(r"\2", text, count=1)
    return _normal(text)


def split_clauses(text: str) -> list[dict[str, str]]:
    """Split numbered clauses, or fall back to non-empty paragraphs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    clauses: list[dict[str, str]] = []
    current: list[str] = []
    current_id = ""
    saw_numbered = False
    for line in text.split("\n"):
        cleaned = line.strip()
        match = _NUMBERED.match(cleaned)
        if match:
            saw_numbered = True
            if current:
                clauses.append({"clause_id": current_id, "text": " ".join(current).strip()})
            current_id = match.group(1).rstrip(".")
            current = [cleaned]
        elif saw_numbered:
            if cleaned:
                current.append(cleaned)
        elif cleaned:
            current.append(cleaned)
        elif current:
            clauses.append({"clause_id": "", "text": " ".join(current).strip()})
            current = []

    if current:
        clauses.append({"clause_id": current_id, "text": " ".join(current).strip()})

    if not saw_numbered:
        return [c for c in clauses if c["text"]]
    return [c for c in clauses if c["text"]]


def risk_level(text: str) -> str | None:
    if any(pattern.search(text) for pattern in _HIGH):
        return "High"
    if any(pattern.search(text) for pattern in _MEDIUM):
        return "Medium"
    if any(pattern.search(text) for pattern in _LOW):
        return "Low"
    return None


def _key_terms(before: str, after: str) -> list[dict[str, str]]:
    left = [m.group(0).strip() for m in _AMOUNTS.finditer(before)]
    right = [m.group(0).strip() for m in _AMOUNTS.finditer(after)]
    terms = []
    for index in range(max(len(left), len(right))):
        old = left[index] if index < len(left) else "—"
        new = right[index] if index < len(right) else "—"
        if old.casefold() != new.casefold():
            terms.append({"before": old, "after": new})
    return terms


def _word_diff(before: str, after: str) -> list[dict[str, str]]:
    old_tokens = re.findall(r"\s+|[^\s]+", before)
    new_tokens = re.findall(r"\s+|[^\s]+", after)
    chunks = []
    for tag, a1, a2, b1, b2 in SequenceMatcher(None, old_tokens, new_tokens, autojunk=False).get_opcodes():
        if tag in ("equal", "delete", "replace") and a1 != a2:
            chunks.append({"kind": "removed" if tag != "equal" else "same", "text": "".join(old_tokens[a1:a2])})
        if tag in ("insert", "replace") and b1 != b2:
            chunks.append({"kind": "added", "text": "".join(new_tokens[b1:b2])})
    return chunks


def _pair_clauses(old: list[dict], new: list[dict]):
    """Pair matching text first, then same headings / most similar clauses."""
    pairs: list[tuple[int | None, int | None, str]] = []
    old_free = set(range(len(old)))
    new_free = set(range(len(new)))

    # Sequence matching preserves unchanged clauses when an insertion shifts
    # their displayed numbers/positions; exact leftovers are true moves.
    old_signatures = [_body_signature(c["text"]) for c in old]
    new_signatures = [_body_signature(c["text"]) for c in new]
    for block in SequenceMatcher(None, old_signatures, new_signatures, autojunk=False).get_matching_blocks():
        for offset in range(block.size):
            oi, ni = block.a + offset, block.b + offset
            pairs.append((oi, ni, "unchanged"))
            old_free.discard(oi)
            new_free.discard(ni)
    for oi in sorted(tuple(old_free)):
        signature = old_signatures[oi]
        match = next((ni for ni in sorted(new_free) if new_signatures[ni] == signature), None)
        if match is not None:
            pairs.append((oi, match, "moved"))
            old_free.remove(oi)
            new_free.remove(match)

    # If clause numbers/labels agree, treat changed wording as a modification.
    for oi in sorted(tuple(old_free)):
        clause_id = old[oi]["clause_id"]
        if not clause_id:
            continue
        ni = next((n for n in sorted(new_free) if new[n]["clause_id"] == clause_id), None)
        if ni is not None:
            pairs.append((oi, ni, "modified"))
            old_free.remove(oi)
            new_free.remove(ni)

    # Greedy best similarity handles unnumbered clauses and renumbering.
    candidates = []
    for oi in old_free:
        for ni in new_free:
            ratio = SequenceMatcher(None, _body_signature(old[oi]["text"]),
                                    _body_signature(new[ni]["text"])).ratio()
            if ratio >= 0.38:
                candidates.append((ratio, oi, ni))
    for _, oi, ni in sorted(candidates, reverse=True):
        if oi in old_free and ni in new_free:
            pairs.append((oi, ni, "modified"))
            old_free.remove(oi)
            new_free.remove(ni)

    pairs.extend((oi, None, "removed") for oi in sorted(old_free))
    pairs.extend((None, ni, "added") for ni in sorted(new_free))
    return sorted(pairs, key=lambda p: (p[1] if p[1] is not None else 10**6,
                                        p[0] if p[0] is not None else 10**6))


def _risk_delta(status: str, before: str, after: str, old_level, new_level):
    weights = {None: 0, "Low": 1, "Medium": 2, "High": 5}
    protection_removed = status == "removed" and bool(_PROTECTIVE.search(before))
    if protection_removed:
        return 5, "Protection removed"
    delta = weights[new_level] - weights[old_level]
    if status == "added":
        delta = weights[new_level]
    elif status == "removed":
        delta = -weights[old_level]
    return delta, "Risk increased" if delta > 0 else "Risk decreased" if delta < 0 else "No material risk change"


def compare_contracts(v1: str, v2: str) -> dict:
    if not v1 or not v1.strip() or not v2 or not v2.strip():
        raise ValueError("Both contract versions are required.")
    old = split_clauses(v1)
    new = split_clauses(v2)
    changes = []
    total_delta = 0
    for oi, ni, status in _pair_clauses(old, new):
        before = old[oi]["text"] if oi is not None else ""
        after = new[ni]["text"] if ni is not None else ""
        old_level = risk_level(before) if before else None
        new_level = risk_level(after) if after else None
        delta, risk_change = _risk_delta(status, before, after, old_level, new_level)
        total_delta += delta
        changes.append({
            "status": status,
            "before_text": before,
            "after_text": after,
            "before_risk": old_level,
            "after_risk": new_level,
            "risk_change": risk_change,
            "risk_delta": delta,
            "key_terms": _key_terms(before, after),
            "word_diff": _word_diff(before, after),
            "similarity": round(SequenceMatcher(None, _normal(before), _normal(after)).ratio(), 3)
                if before and after else 0.0,
        })

    counts = {key: sum(1 for item in changes if item["status"] == key)
              for key in ("added", "removed", "modified", "moved", "unchanged")}
    if not any(counts[k] for k in ("added", "removed", "modified", "moved")):
        verdict = "No changes"
    elif total_delta > 0:
        verdict = "Riskier"
    elif total_delta < 0:
        verdict = "Safer"
    else:
        verdict = "No material risk change"
    return {
        "verdict": verdict,
        "risk_score_before": sum({None: 0, "Low": 1, "Medium": 2, "High": 5}[risk_level(c["text"])] for c in old),
        "risk_score_after": sum({None: 0, "Low": 1, "Medium": 2, "High": 5}[risk_level(c["text"])] for c in new),
        "risk_delta": total_delta,
        "summary": counts,
        "changes": changes,
        "disclaimer": DISCLAIMER,
    }
