"""
core/matching_engine.py — Meridian Match AI Matching Engine

Implements a 6-factor weighted scoring model combining TF-IDF cosine similarity
with structured rule-based compatibility and NLP constraint verification.
Factor weights (adaptive via learning_engine, defaults below):
  1. Semantic Product Similarity:  40%
  2. Category Match:               15%
  3. Quantity Fit:                 15%
  4. Budget Compatibility:         15%
  5. Delivery Timeline Fit:        10%
  6. Location Proximity:            5%

Parts 1 & 2 additions:
  - product_fit_semantic_score: informational sentence-embedding similarity (NOT blended)
  - top_terms: top shared TF-IDF terms surfaced in match explanations
Part 4 addition:
  - get_active_weights() replaces hardcoded W_* constants at run time
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
    get_connection,
)
from core.constraint_parser import (
    parse_constraints,
    apply_constraints,
    build_explanation_sentence,
    Constraint,
)
from core.learning_engine import get_active_weights, DEFAULT_WEIGHTS
from theme import LOCATION_STATES

# ── Hardcoded default weights (used when no learned weights exist) ─────────────
W_PRODUCT   = DEFAULT_WEIGHTS["w_product"]
W_CATEGORY  = DEFAULT_WEIGHTS["w_category"]
W_QUANTITY  = DEFAULT_WEIGHTS["w_quantity"]
W_BUDGET    = DEFAULT_WEIGHTS["w_budget"]
W_DELIVERY  = DEFAULT_WEIGHTS["w_delivery"]
W_LOCATION  = DEFAULT_WEIGHTS["w_location"]


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


def _get_city_state(city: str) -> str:
    """Case-insensitive state lookup from LOCATION_STATES dictionary."""
    clean = city.strip().lower()
    for loc_name, state in LOCATION_STATES.items():
        if loc_name.lower() == clean:
            return state
    return "Unknown"


def _score_location(c_city: str, s_city: str) -> float:
    """Proximity score: Same city = 1.0, Same state = 0.6, Different state = 0.3."""
    if c_city.strip().lower() == s_city.strip().lower():
        return 1.0
    c_state = _get_city_state(c_city)
    s_state = _get_city_state(s_city)
    if c_state == s_state and c_state not in ("Unknown", "Other"):
        return 0.6
    return 0.3


def _top_shared_terms(
    vectorizer: TfidfVectorizer,
    client_vec: Any,
    supplier_vec: Any,
    top_k: int = 3,
) -> list[str]:
    """Return top_k feature names where both client and supplier have nonzero TF-IDF weight.

    Uses element-wise minimum of the two sparse vectors as a proxy for shared importance.

    Args:
        vectorizer: Fitted TfidfVectorizer.
        client_vec: Sparse row vector for the client.
        supplier_vec: Sparse row vector for the supplier.
        top_k: Number of top shared terms to return.

    Returns:
        List of up to top_k feature name strings.
    """
    try:
        feature_names = np.array(vectorizer.get_feature_names_out())
        c_arr = np.asarray(client_vec.todense()).flatten()
        s_arr = np.asarray(supplier_vec.todense()).flatten()
        shared = np.minimum(c_arr, s_arr)
        top_indices = shared.argsort()[::-1][:top_k]
        return [str(feature_names[i]) for i in top_indices if shared[i] > 0]
    except Exception:
        return []


def _evaluate_and_save_pair(
    client: sqlite3.Row,
    supplier: sqlite3.Row,
    client_vec: Any,
    supplier_vec: Any,
    client_constraints: list[Constraint],
    vectorizer: TfidfVectorizer,
    weights: dict[str, float],
    semantic_sim: float | None = None,
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
        weights["w_product"] * f1 + weights["w_category"] * f2 + weights["w_quantity"] * f3 +
        weights["w_budget"] * f4 + weights["w_delivery"] * f5 + weights["w_location"] * f6
    )

    s_text = f"{supplier['product_offered']} {supplier['additional_notes'] or ''}"
    adj_score, penalty_applied, constraint_details = apply_constraints(base_score, client_constraints, s_text)

    # ── Part 2: top shared TF-IDF terms ──────────────────────────────────────
    top_terms_list = _top_shared_terms(vectorizer, client_vec, supplier_vec, top_k=3)
    top_terms_str = ", ".join(top_terms_list) if top_terms_list else None

    explanation = build_explanation_sentence(
        adj_score, f1, f4, f5, f3, constraint_details, top_terms=top_terms_list
    )

    # ── Part 1: semantic score (informational only, NOT blended into weighted sum) ─
    semantic_score = semantic_sim  # passed in from caller; may be None

    match_id = upsert_match(
        client_id=client["id"], supplier_id=supplier["id"],
        overall_score=round(adj_score, 2), product_fit_score=round(f1, 2),
        category_score=round(f2, 2), quantity_score=round(f3, 2),
        budget_score=round(f4, 2), delivery_score=round(f5, 2),
        location_score=round(f6, 2), constraint_penalty_applied=int(penalty_applied),
        explanation_text=explanation,
        product_fit_semantic_score=round(semantic_score * 100, 2) if semantic_score is not None else None,
        top_terms=top_terms_str,
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
        "product_fit_semantic_score": round(semantic_score * 100, 2) if semantic_score is not None else None,
        "top_terms": top_terms_str,
    }


def run_matching_for_client(client_id: int) -> list[dict[str, Any]]:
    """Compute and persist matches for a single client against all active suppliers."""
    clients = get_all_clients(completed_only=True)
    suppliers = get_all_suppliers(completed_only=True)
    target = next((c for c in clients if c["id"] == client_id), None)
    if not target or not suppliers:
        return []

    conn = get_connection()
    weights = get_active_weights(conn)
    conn.close()

    corpus, _, _ = _build_corpus(clients, suppliers)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)
    tfidf = vectorizer.fit_transform(corpus)

    c_idx = next(i for i, c in enumerate(clients) if c["id"] == client_id)
    c_vec = tfidf[c_idx]
    c_constraints = parse_constraints(target["additional_notes"] or "")

    # Semantic embeddings (Part 1) — computed in batch for efficiency
    from core.embedding_engine import get_embeddings_batch, EMBEDDINGS_AVAILABLE
    semantic_sims: list[float | None] = [None] * len(suppliers)
    if EMBEDDINGS_AVAILABLE:
        c_text = f"{target['product_requirement']} {target['additional_notes'] or ''}".strip()
        s_texts = [f"{s['product_offered']} {s['additional_notes'] or ''}".strip() for s in suppliers]
        all_texts = [c_text] + s_texts
        embeddings = get_embeddings_batch(all_texts)
        if embeddings is not None:
            c_emb = embeddings[0]
            for i in range(len(suppliers)):
                semantic_sims[i] = float(np.dot(c_emb, embeddings[i + 1]))

    results = []
    for s_idx, supplier in enumerate(suppliers):
        s_vec = tfidf[len(clients) + s_idx]
        res = _evaluate_and_save_pair(
            target, supplier, c_vec, s_vec, c_constraints, vectorizer, weights,
            semantic_sim=semantic_sims[s_idx],
        )
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

    conn = get_connection()
    weights = get_active_weights(conn)
    conn.close()

    corpus, _, _ = _build_corpus(clients, suppliers)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)
    tfidf = vectorizer.fit_transform(corpus)

    s_idx = next(i for i, s in enumerate(suppliers) if s["id"] == supplier_id)
    s_vec = tfidf[len(clients) + s_idx]

    # Semantic embeddings — batch for all clients
    from core.embedding_engine import get_embeddings_batch, EMBEDDINGS_AVAILABLE
    semantic_sims: list[float | None] = [None] * len(clients)
    if EMBEDDINGS_AVAILABLE:
        s_text = f"{target['product_offered']} {target['additional_notes'] or ''}".strip()
        c_texts = [f"{c['product_requirement']} {c['additional_notes'] or ''}".strip() for c in clients]
        all_texts = c_texts + [s_text]
        embeddings = get_embeddings_batch(all_texts)
        if embeddings is not None:
            s_emb = embeddings[-1]
            for i in range(len(clients)):
                semantic_sims[i] = float(np.dot(embeddings[i], s_emb))

    results = []
    for c_idx, client in enumerate(clients):
        c_vec = tfidf[c_idx]
        c_constraints = parse_constraints(client["additional_notes"] or "")
        res = _evaluate_and_save_pair(
            client, target, c_vec, s_vec, c_constraints, vectorizer, weights,
            semantic_sim=semantic_sims[c_idx],
        )
        results.append(res)

    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results


def run_full_matching() -> int:
    """Recompute all match scores across all active client-supplier pairs."""
    clients = get_all_clients(completed_only=True)
    suppliers = get_all_suppliers(completed_only=True)
    if not clients or not suppliers:
        return 0

    conn = get_connection()
    weights = get_active_weights(conn)
    conn.close()

    corpus, _, _ = _build_corpus(clients, suppliers)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True)
    tfidf = vectorizer.fit_transform(corpus)

    # Semantic embeddings — full batch
    from core.embedding_engine import get_embeddings_batch, EMBEDDINGS_AVAILABLE
    all_texts = [
        f"{c['product_requirement']} {c['additional_notes'] or ''}".strip() for c in clients
    ] + [
        f"{s['product_offered']} {s['additional_notes'] or ''}".strip() for s in suppliers
    ]
    embeddings = get_embeddings_batch(all_texts) if EMBEDDINGS_AVAILABLE else None

    count = 0
    for c_idx, client in enumerate(clients):
        c_vec = tfidf[c_idx]
        c_constraints = parse_constraints(client["additional_notes"] or "")
        c_emb = embeddings[c_idx] if embeddings is not None else None
        for s_idx, supplier in enumerate(suppliers):
            s_vec = tfidf[len(clients) + s_idx]
            semantic_sim: float | None = None
            if c_emb is not None and embeddings is not None:
                semantic_sim = float(np.dot(c_emb, embeddings[len(clients) + s_idx]))
            _evaluate_and_save_pair(
                client, supplier, c_vec, s_vec, c_constraints, vectorizer, weights,
                semantic_sim=semantic_sim,
            )
            count += 1

    return count
