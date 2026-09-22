"""
core/category_classifier.py — Meridian Match Category Classifier

Trains a TF-IDF + LogisticRegression pipeline on existing client/supplier
free-text profiles labeled by their own chosen category dropdown.
Predicts the most likely category for new profiles and surfaces mismatches
as a non-blocking advisory warning.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

MIN_SAMPLES = 10  # Minimum total labeled samples to train


def train_classifier(db_conn: sqlite3.Connection) -> Pipeline | None:
    """Train a TF-IDF + LogisticRegression classifier on profile free-text.

    Fetches all clients and suppliers that have both free-text descriptions
    and a category label, then trains a sklearn Pipeline.

    Args:
        db_conn: Active SQLite connection.

    Returns:
        Fitted sklearn Pipeline, or None if fewer than MIN_SAMPLES samples.
    """
    rows: list[tuple[str, str]] = []

    # Collect client texts + labels
    for row in db_conn.execute(
        "SELECT product_requirement, additional_notes, category FROM clients "
        "WHERE profile_complete=1 AND category != '' AND product_requirement != ''"
    ).fetchall():
        text = f"{row['product_requirement']} {row['additional_notes'] or ''}".strip()
        rows.append((text, row["category"]))

    # Collect supplier texts + labels
    for row in db_conn.execute(
        "SELECT product_offered, additional_notes, category FROM suppliers "
        "WHERE profile_complete=1 AND category != '' AND product_offered != ''"
    ).fetchall():
        text = f"{row['product_offered']} {row['additional_notes'] or ''}".strip()
        rows.append((text, row["category"]))

    if len(rows) < MIN_SAMPLES:
        return None

    texts = [r[0] for r in rows]
    labels = [r[1] for r in rows]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=500, C=1.0, solver="lbfgs")),
    ])
    pipeline.fit(texts, labels)
    return pipeline


def predict_category(text: str, pipeline: Pipeline) -> tuple[str, float]:
    """Predict the most likely category for a free-text profile.

    Args:
        text: Combined product description + notes string.
        pipeline: Fitted sklearn Pipeline from train_classifier().

    Returns:
        Tuple of (predicted_label, confidence) where confidence is in [0, 1].
    """
    if not text.strip():
        return ("", 0.0)
    proba = pipeline.predict_proba([text])[0]
    best_idx = int(np.argmax(proba))
    label = pipeline.classes_[best_idx]
    confidence = float(proba[best_idx])
    return (str(label), confidence)


def get_classifier_accuracy(db_conn: sqlite3.Connection) -> str:
    """Compute cross-validated accuracy of the category classifier.

    Returns a formatted percentage string, or 'N/A' if insufficient data.

    Args:
        db_conn: Active SQLite connection.

    Returns:
        String like '87.3%' or 'N/A'.
    """
    rows: list[tuple[str, str]] = []
    for row in db_conn.execute(
        "SELECT product_requirement, additional_notes, category FROM clients "
        "WHERE profile_complete=1 AND category != '' AND product_requirement != ''"
    ).fetchall():
        text = f"{row['product_requirement']} {row['additional_notes'] or ''}".strip()
        rows.append((text, row["category"]))
    for row in db_conn.execute(
        "SELECT product_offered, additional_notes, category FROM suppliers "
        "WHERE profile_complete=1 AND category != '' AND product_offered != ''"
    ).fetchall():
        text = f"{row['product_offered']} {row['additional_notes'] or ''}".strip()
        rows.append((text, row["category"]))

    if len(rows) < MIN_SAMPLES:
        return "N/A"

    texts = [r[0] for r in rows]
    labels = [r[1] for r in rows]
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=500, C=1.0, solver="lbfgs")),
    ])
    cv = min(3, len(set(labels)))
    if cv < 2:
        return "N/A"
    try:
        scores = cross_val_score(pipeline, texts, labels, cv=cv, scoring="accuracy")
        return f"{scores.mean() * 100:.1f}%"
    except Exception:
        return "N/A"


def get_or_train_classifier(db_conn: sqlite3.Connection) -> Pipeline | None:
    """Streamlit-cache-compatible wrapper — train or retrieve the classifier.

    In Streamlit context this should be wrapped with @st.cache_resource at
    the call site.  Returns None if insufficient data.
    """
    return train_classifier(db_conn)
