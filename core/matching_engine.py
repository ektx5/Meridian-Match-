"""
core/matching_engine.py — Meridian Match AI Matching Engine

Implements a 6-factor weighted scoring model combining TF-IDF cosine similarity
with structured rule-based compatibility and NLP constraint verification.
Factor weights:
  1. Semantic Product Similarity:  40%
  2. Category Match:               15%
  3. Quantity Fit:                 15%
  4. Budget Compatibility:         15%
  5. Delivery Timeline Fit:        10%
  6. Location Proximity:            5%
"""

from __future__ import annotations

import math
import sqlite3
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.database import (
    get_all_clients,
    get_all_suppliers,
    upsert_match,
    insert_match_explanation,
    delete_explanations_for_match,
)
from core.constraint_parser import (
    parse_constraints,
    apply_constraints,
    build_explanation_sentence,
    Constraint,
)
from theme import LOCATION_STATES

W_PRODUCT   = 0.40
W_CATEGORY  = 0.15
W_QUANTITY  = 0.15
W_BUDGET    = 0.15
W_DELIVERY  = 0.10
W_LOCATION  = 0.05


def _build_corpus(clients: list[sqlite3.Row], suppliers: list[sqlite3.Row]) -> tuple[list[str], list[str], list[str]]:
    """Combine product descriptions and notes for TF-IDF corpus fitting."""
    c_texts = [f"{c['product_requirement']} {c['additional_notes'] or ''}".strip() for c in clients]
    s_texts = [f"{s['product_offered']} {s['additional_notes'] or ''}".strip() for s in suppliers]
    return c_texts + s_texts, c_texts, s_texts


def _score_quantity(required: float, available: float) -> float:
    """Score available quantity coverage. Full score if >= 100%, decay below, steep penalty under 50%."""
    if required <= 0 or available <= 0:
        return 0.0
    ratio = available / required
    if ratio >= 1.0:
        return 1.0
    elif ratio >= 0.5:
        return 0.6 + (ratio - 0.5) * 0.8
    return ratio * 0.6


def _score_budget_single(c_min: float, c_max: float, s_min: float, s_max: float) -> float:
    """Calculate proportional overlap between two budget/price intervals."""
    if c_max <= 0 or s_max <= 0 or c_max < c_min or s_max < s_min:
        return 0.0
    overlap_start = max(c_min, s_min)
    overlap_end = min(c_max, s_max)
    overlap = max(0.0, overlap_end - overlap_start)
    s_range = max(1.0, s_max - s_min)
    return min(1.0, overlap / s_range)


def _score_budget(c_min: float, c_max: float, c_qty: float, s_min: float, s_max: float) -> float:
    """Score budget compatibility handling both total project budget and per-unit pricing."""
    score_direct = _score_budget_single(c_min, c_max, s_min, s_max)
    if c_qty > 0:
        score_per_unit = _score_budget_single(c_min / c_qty, c_max / c_qty, s_min, s_max)
        score_total = _score_budget_single(c_min, c_max, s_min * c_qty, s_max * c_qty)
        return max(score_direct, score_per_unit, score_total)
    return score_direct


def _score_delivery(c_days: int, s_days: int) -> float:
    """Full score if supplier meets client timeline, exponential decay if slower."""
    if c_days <= 0 or s_days <= 0:
        return 0.5
    if s_days <= c_days:
        return 1.0
    excess_ratio = (s_days - c_days) / max(1, c_days)
    return max(0.0, float(math.exp(-1.2 * excess_ratio)))


def _score_location(c_city: str, s_city: str) -> float:
    """Proximity score: Same city = 1.0, Same state = 0.6, Different state = 0.3."""
    if c_city.strip().lower() == s_city.strip().lower():
        return 1.0
    c_state = LOCATION_STATES.get(c_city.strip(), "Unknown")
    s_state = LOCATION_STATES.get(s_city.strip(), "Unknown")
    if c_state == s_state and c_state not in ("Unknown", "Other"):
        return 0.6
    return 0.3


def _evaluate_and_save_pair(
    client: sqlite3.Row,
    supplier: sqlite3.Row,
    client_vec: Any,
    supplier_vec: Any,
    client_constraints: list[Constraint],
) -> dict[str, Any]:
    """Compute all 6 factors, apply constraint adjustments, and upsert match record."""
    sim = cosine_similarity(client_vec, supplier_vec)[0][0]
    f1 = float(np.clip(sim, 0.0, 1.0)) * 100.0

    f2 = 100.0 if client["category"].strip() == supplier["category"].strip() else 0.0

    f3 = _score_quantity(float(client["quantity_required"]), float(supplier["available_quantity"])) * 100.0

    f4 = _score_budget(
        float(client["budget_min"]), float(client["budget_max"]),
        float(client["quantity_required"]),
        float(supplier["price_min"]), float(supplier["price_max"]),
    ) * 100.0

    f5 = _score_delivery(int(client["delivery_days"]), int(supplier["delivery_days"])) * 100.0
    f6 = _score_location(client["location"], supplier["location"]) * 100.0

    base_score = (
        W_PRODUCT * f1 + W_CATEGORY * f2 + W_QUANTITY * f3 +
        W_BUDGET * f4 + W_DELIVERY * f5 + W_LOCATION * f6
    )

    s_text = f"{supplier['product_offered']} {supplier['additional_notes'] or ''}"
    adj_score, penalty_applied, constraint_details = apply_constraints(base_score, client_constraints, s_text)

    explanation = build_explanation_sentence(adj_score, f1, f4, f5, f3, constraint_details)

    match_id = upsert_match(
        client_id=client["id"], supplier_id=supplier["id"],
        overall_score=round(adj_score, 2), product_fit_score=round(f1, 2),
        category_score=round(f2, 2), quantity_score=round(f3, 2),
        budget_score=round(f4, 2), delivery_score=round(f5, 2),
        location_score=round(f6, 2), constraint_penalty_applied=int(penalty_applied),
        explanation_text=explanation,
    )

    delete_explanations_for_match(match_id)
    for d in constraint_details:
        insert_match_explanation(match_id, d["type"], d["phrase"], bool(d["satisfied"]))

    return {
        "match_id": match_id, "client_id": client["id"], "supplier_id": supplier["id"],
        "supplier_name": supplier["supplier_name"], "company_name": client["company_name"],
        "overall_score": round(adj_score, 2), "product_fit_score": round(f1, 2),
        "category_score": round(f2, 2), "quantity_score": round(f3, 2),
        "budget_score": round(f4, 2), "delivery_score": round(f5, 2),
        "location_score": round(f6, 2), "constraint_penalty_applied": int(penalty_applied),
        "explanation_text": explanation, "constraint_details": constraint_details,
    }


def run_matching_for_client(client_id: int) -> list[dict[str, Any]]:
    """Compute and persist matches for a single client against all active suppliers."""
    clients = get_all_clients(completed_only=True)
    suppliers = get_all_suppliers(completed_only=True)
    target = next((c for c in clients if c["id"] == client_id), None)
    if not target or not suppliers:
        return []

    corpus, _, _ = _build_corpus(clients, suppliers)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)
    tfidf = vectorizer.fit_transform(corpus)

    c_idx = next(i for i, c in enumerate(clients) if c["id"] == client_id)
    c_vec = tfidf[c_idx]
    c_constraints = parse_constraints(target["additional_notes"] or "")

    results = []
    for s_idx, supplier in enumerate(suppliers):
        s_vec = tfidf[len(clients) + s_idx]
        res = _evaluate_and_save_pair(target, supplier, c_vec, s_vec, c_constraints)
        results.append(res)

    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results


def run_matching_for_supplier(supplier_id: int) -> list[dict[str, Any]]:
    """Compute and persist matches for a single supplier against all active clients."""
    clients = get_all_clients(completed_only=True)
    suppliers = get_all_suppliers(completed_only=True)
    target = next((s for s in suppliers if s["id"] == supplier_id), None)
    if not target or not clients:
        return []

    corpus, _, _ = _build_corpus(clients, suppliers)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)
    tfidf = vectorizer.fit_transform(corpus)

    s_idx = next(i for i, s in enumerate(suppliers) if s["id"] == supplier_id)
    s_vec = tfidf[len(clients) + s_idx]

    results = []
    for c_idx, client in enumerate(clients):
        c_vec = tfidf[c_idx]
        c_constraints = parse_constraints(client["additional_notes"] or "")
        res = _evaluate_and_save_pair(client, target, c_vec, s_vec, c_constraints)
        results.append(res)

    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results


def run_full_matching() -> int:
    """Recompute all match scores across all active client-supplier pairs."""
    clients = get_all_clients(completed_only=True)
    suppliers = get_all_suppliers(completed_only=True)
    if not clients or not suppliers:
        return 0

    corpus, _, _ = _build_corpus(clients, suppliers)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)
    tfidf = vectorizer.fit_transform(corpus)

    count = 0
    for c_idx, client in enumerate(clients):
        c_vec = tfidf[c_idx]
        c_constraints = parse_constraints(client["additional_notes"] or "")
        for s_idx, supplier in enumerate(suppliers):
            s_vec = tfidf[len(clients) + s_idx]
            _evaluate_and_save_pair(client, supplier, c_vec, s_vec, c_constraints)
            count += 1

    return count
