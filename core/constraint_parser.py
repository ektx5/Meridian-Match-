"""
core/constraint_parser.py — Meridian Match NLP Constraint Parser

Extracts DEAL-BREAKER constraints ("must", "required", "mandatory") and
NICE-TO-HAVE preferences ("prefer", "ideally", "bonus if") from client notes,
then verifies satisfaction against supplier text to adjust final match scores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

DEAL_BREAKER_TRIGGERS: list[str] = [
    r"\bmust\b", r"\brequir\w*\b", r"\bmandatory\b", r"\bonly\b",
    r"\bno exceptions?\b", r"\bcertif\w*\b",
    r"\bstrictly\b", r"\bcompulsory\b", r"\bguaranteed\b",
]

NICE_TO_HAVE_TRIGGERS: list[str] = [
    r"\bprefer\b", r"\bpreferably\b", r"\bideally\b",
    r"\bwould be nice\b", r"\bbonus if\b", r"\bnice to have\b",
    r"\bif possible\b", r"\bif available\b", r"\bwelcome\b",
]

DEAL_BREAKER_COMPILED = [re.compile(t, re.IGNORECASE) for t in DEAL_BREAKER_TRIGGERS]
NICE_TO_HAVE_COMPILED = [re.compile(t, re.IGNORECASE) for t in NICE_TO_HAVE_TRIGGERS]

# Words stripped before matching to avoid false positives on generic certification words
GENERIC_STOP_WORDS = {
    "be", "is", "are", "the", "a", "an", "in", "on", "at", "by", "for", "with",
    "from", "to", "of", "and", "or", "not", "we", "our", "that", "this", "all",
    "must", "only", "should", "will", "have", "has", "it", "if", "can", "do",
    "required", "mandatory", "preferred", "ideally", "prefer", "certified",
    "certification", "certifications", "compliant", "compliance", "supplier",
    "suppliers", "standard", "standards", "requirement", "requirements", "product",
}

DEAL_BREAKER_PENALTY_MULTIPLIER: float = 0.40
NICE_TO_HAVE_BONUS_POINTS: float = 5.0


@dataclass
class Constraint:
    """Parsed requirement or preference from client notes."""
    constraint_type: str   # 'deal_breaker' | 'nice_to_have'
    raw_text: str
    phrase: str


def _extract_phrase(clause: str, trigger_match: re.Match[str]) -> str:
    """Extract and clean the key phrase following a trigger word in a clause."""
    after_trigger = clause[trigger_match.end():].strip()
    cut = re.split(r"[.,;:\n]", after_trigger, maxsplit=1)[0].strip()
    if len(cut) < 3:
        cut = clause.strip()
    phrase = re.sub(r"\s+", " ", cut)
    # Remove leading filler verbs like "be", "have"
    phrase = re.sub(r"^(be|have|provide|use)\s+", "", phrase, flags=re.IGNORECASE)
    return phrase[:120].strip()


def parse_constraints(notes_text: str) -> list[Constraint]:
    """Parse client notes into Constraint dataclasses (deal_breaker / nice_to_have)."""
    if not notes_text or not notes_text.strip():
        return []

    clauses = re.split(r"[.;!\n]+", notes_text)
    constraints: list[Constraint] = []
    seen: set[str] = set()

    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue

        tagged = False
        for pattern in DEAL_BREAKER_COMPILED:
            m = pattern.search(clause)
            if m:
                phrase = _extract_phrase(clause, m)
                key = phrase.lower()[:35]
                if key not in seen:
                    seen.add(key)
                    constraints.append(Constraint("deal_breaker", clause, phrase))
                tagged = True
                break

        if tagged:
            continue

        for pattern in NICE_TO_HAVE_COMPILED:
            m = pattern.search(clause)
            if m:
                phrase = _extract_phrase(clause, m)
                key = phrase.lower()[:35]
                if key not in seen:
                    seen.add(key)
                    constraints.append(Constraint("nice_to_have", clause, phrase))
                break

    return constraints


def check_constraint_satisfied(constraint_phrase: str, supplier_text: str) -> bool:
    """
    Check whether the supplier's product text satisfies the extracted constraint.
    Enforces exact matches for industry standards, certifications, and acronyms.
    """
    s_low = supplier_text.lower()
    p_low = constraint_phrase.lower()

    # 1. Acronyms & industry standard codes (e.g. GOTS, ISO, RoHS, BIFMA, FSC, FSSAI, CE, REACH, UL)
    acronyms = re.findall(r"\b[A-Z][A-Z0-9\-]{1,15}\b", constraint_phrase)
    # Filter out false-positive common uppercase words like 'A', 'I', 'WE'
    valid_acronyms = [a for a in acronyms if a.lower() not in {"we", "our", "the", "and", "for"}]

    # Numbers like 9001, 14001, 1642, 100, 53
    numbers = re.findall(r"\b\d{2,6}\b", constraint_phrase)

    # If formal standards/numbers are present, verify they exist in supplier text
    if valid_acronyms or numbers:
        all_acronyms_found = all(a.lower() in s_low for a in valid_acronyms)
        all_numbers_found = all(n in s_low for n in numbers)
        return all_acronyms_found and all_numbers_found

    # 2. General descriptive phrases (e.g. 'eco-friendly packaging', 'organic cotton')
    words = set(re.findall(r"\b[a-z]{2,}\b", p_low)) - GENERIC_STOP_WORDS
    if not words:
        # Fallback to direct substring match
        return p_low in s_low

    s_tokens = set(re.findall(r"\b[a-z]{2,}\b", s_low))
    overlap = words & s_tokens
    # If phrase is short (1-2 words), require at least one key word; if more, require >= 40%
    return len(overlap) >= 1 if len(words) <= 2 else (len(overlap) / len(words)) >= 0.4


def apply_constraints(
    base_score: float, constraints: list[Constraint], supplier_text: str
) -> tuple[float, bool, list[dict[str, Any]]]:
    """Apply deal-breaker penalties (x0.4) and nice-to-have bonuses (+5 pts) to base score."""
    adjusted = base_score
    penalty_applied = False
    details: list[dict[str, Any]] = []

    for c in constraints:
        satisfied = check_constraint_satisfied(c.phrase, supplier_text)
        if c.constraint_type == "deal_breaker":
            if not satisfied:
                adjusted *= DEAL_BREAKER_PENALTY_MULTIPLIER
                penalty_applied = True
                note = f"⚠️ Missing required: {c.phrase}"
            else:
                note = f"✓ Required met: {c.phrase}"
        else:
            if satisfied:
                adjusted = min(100.0, adjusted + NICE_TO_HAVE_BONUS_POINTS)
                note = f"✓ Bonus: {c.phrase}"
            else:
                note = f"○ Optional not met: {c.phrase}"

        details.append({
            "type": c.constraint_type, "phrase": c.phrase,
            "satisfied": satisfied, "note": note,
        })

    adjusted = max(0.0, min(100.0, adjusted))
    return adjusted, penalty_applied, details


def build_explanation_sentence(
    overall_score: float, product_fit: float, budget_score: float,
    delivery_score: float, quantity_score: float, constraint_details: list[dict[str, Any]],
    top_terms: list[str] | None = None,
) -> str:
    """Build an auto-generated plain-English template summary of the match."""
    if overall_score >= 80:
        quality = "Strong match"
    elif overall_score >= 60:
        quality = "Good match"
    elif overall_score >= 40:
        quality = "Moderate match"
    else:
        quality = "Weak match"

    traits: list[str] = []
    if product_fit >= 70:
        traits.append("product needs align closely")
    elif product_fit >= 40:
        traits.append("product requirements partially align")
    else:
        traits.append("product alignment is limited")

    if budget_score >= 75:
        traits.append("budget is fully compatible")
    elif budget_score >= 40:
        traits.append("budget partially overlaps")
    else:
        traits.append("budget ranges may not align")

    if delivery_score >= 80:
        traits.append("delivery timeline is achievable")
    elif delivery_score < 40:
        traits.append("delivery timeline may be tight")

    if quantity_score < 50:
        traits.append("available quantity falls short")

    sentence = f"{quality} ({overall_score:.0f}%) — {', '.join(traits)}."

    missed = [d["note"] for d in constraint_details if not d["satisfied"] and d["type"] == "deal_breaker"]
    bonuses = [d["note"] for d in constraint_details if d["satisfied"] and d["type"] == "nice_to_have"]

    if missed:
        sentence += f" {' '.join(missed)}"
    if bonuses:
        sentence += f" {' '.join(bonuses)}"
    if top_terms:
        sentence += f" Key terms: {', '.join(top_terms)}."

    return sentence
