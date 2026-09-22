"""
core/learning_engine.py — Meridian Match Adaptive Weight Learning

Uses feedback from confirmed/rejected match statuses to learn optimal
factor weights via LogisticRegression. Weights are persisted in the
learned_weights table and retrieved by the matching engine at run time.

Falls back to hardcoded defaults when fewer than 20 labeled samples exist.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# ── Default hardcoded weights (matching_engine.py constants) ─────────────────
DEFAULT_WEIGHTS: dict[str, float] = {
    "w_product":  0.40,
    "w_category": 0.15,
    "w_quantity": 0.15,
    "w_budget":   0.15,
    "w_delivery": 0.10,
    "w_location": 0.05,
}

MIN_LABELED_SAMPLES = 20
FACTOR_COLS = ["product_fit_score", "category_score", "quantity_score",
               "budget_score", "delivery_score", "location_score"]


def get_labeled_training_data(db_conn: sqlite3.Connection) -> pd.DataFrame:
    """Return matches with Confirmed/Rejected status joined with factor scores.

    Args:
        db_conn: Active SQLite connection.

    Returns:
        DataFrame with columns: factor scores + 'label' (1=Confirmed, 0=Rejected).
    """
    rows = db_conn.execute(
        """SELECT m.product_fit_score, m.category_score, m.quantity_score,
                  m.budget_score, m.delivery_score, m.location_score,
                  m.status
           FROM matches m
           WHERE m.status IN ('Confirmed', 'Rejected')"""
    ).fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([dict(r) for r in rows])
    df["label"] = (df["status"] == "Confirmed").astype(int)
    return df[FACTOR_COLS + ["label"]]


def learn_optimal_weights(df: pd.DataFrame) -> dict[str, float]:
    """Estimate optimal factor weights from labeled match data.

    Trains LogisticRegression on 6 factor scores to predict 'Confirmed'.
    Converts coefficients to positive normalized weights summing to 1.0.
    Falls back to DEFAULT_WEIGHTS if insufficient samples or training fails.

    Args:
        df: DataFrame from get_labeled_training_data().

    Returns:
        Dict mapping weight keys (w_product, etc.) to floats summing to 1.0.
    """
    if df.empty or len(df) < MIN_LABELED_SAMPLES:
        return DEFAULT_WEIGHTS.copy()

    X = df[FACTOR_COLS].values
    y = df["label"].values

    if len(set(y)) < 2:
        # All same label — can't distinguish features
        return DEFAULT_WEIGHTS.copy()

    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        clf = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
        clf.fit(X_scaled, y)

        # Use abs(coefficients) as importance signals
        coefs = np.abs(clf.coef_[0])
        if coefs.sum() == 0:
            return DEFAULT_WEIGHTS.copy()
        normalized = coefs / coefs.sum()

        keys = ["w_product", "w_category", "w_quantity", "w_budget", "w_delivery", "w_location"]
        return {k: float(round(v, 4)) for k, v in zip(keys, normalized)}
    except Exception:
        return DEFAULT_WEIGHTS.copy()


def get_active_weights(db_conn: sqlite3.Connection) -> dict[str, float]:
    """Return the most recently learned weights, or defaults if none saved.

    Args:
        db_conn: Active SQLite connection.

    Returns:
        Dict with keys w_product, w_category, w_quantity, w_budget, w_delivery, w_location.
    """
    try:
        row = db_conn.execute(
            """SELECT w_product, w_category, w_quantity, w_budget, w_delivery, w_location
               FROM learned_weights ORDER BY id DESC LIMIT 1"""
        ).fetchone()
        if row:
            return {
                "w_product":  float(row["w_product"]),
                "w_category": float(row["w_category"]),
                "w_quantity": float(row["w_quantity"]),
                "w_budget":   float(row["w_budget"]),
                "w_delivery": float(row["w_delivery"]),
                "w_location": float(row["w_location"]),
            }
    except Exception:
        pass
    return DEFAULT_WEIGHTS.copy()


def save_learned_weights(db_conn: sqlite3.Connection, weights: dict[str, float]) -> None:
    """Persist a new row of learned weights to the learned_weights table.

    Args:
        db_conn: Active SQLite connection.
        weights: Dict from learn_optimal_weights().
    """
    computed_at = datetime.now(timezone.utc).isoformat()
    db_conn.execute(
        """INSERT INTO learned_weights
           (computed_at, w_product, w_category, w_quantity, w_budget, w_delivery, w_location)
           VALUES (?,?,?,?,?,?,?)""",
        (
            computed_at,
            weights.get("w_product",  DEFAULT_WEIGHTS["w_product"]),
            weights.get("w_category", DEFAULT_WEIGHTS["w_category"]),
            weights.get("w_quantity", DEFAULT_WEIGHTS["w_quantity"]),
            weights.get("w_budget",   DEFAULT_WEIGHTS["w_budget"]),
            weights.get("w_delivery", DEFAULT_WEIGHTS["w_delivery"]),
            weights.get("w_location", DEFAULT_WEIGHTS["w_location"]),
        ),
    )
    db_conn.commit()
