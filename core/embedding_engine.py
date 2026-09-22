"""
core/embedding_engine.py — Meridian Match Semantic Embedding Engine

Provides sentence embedding similarity using 'all-MiniLM-L6-v2'.
Falls back gracefully if sentence-transformers is not installed.

EMBEDDINGS_AVAILABLE is True only when the package loads successfully.
"""

from __future__ import annotations

import numpy as np

# ── Optional import — graceful fallback if not installed ──────────────────────
EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None  # type: ignore


def load_embedding_model():
    """Load the MiniLM embedding model (cached via st.cache_resource).

    Returns the model if sentence-transformers is available, else None.
    Must be called inside a Streamlit context for caching to work.
    Wrapped in st.spinner() at call site for first-run UX.
    """
    if not EMBEDDINGS_AVAILABLE or SentenceTransformer is None:
        return None
    try:
        import streamlit as st

        @st.cache_resource(show_spinner=False)
        def _load():
            return SentenceTransformer("all-MiniLM-L6-v2")

        return _load()
    except Exception:
        return None


def get_embedding_similarity(text_a: str, text_b: str) -> float | None:
    """Return cosine similarity [0.0–1.0] between two texts, or None if unavailable.

    Args:
        text_a: First text string.
        text_b: Second text string.

    Returns:
        Float in [0, 1] or None if model not available.
    """
    model = load_embedding_model()
    if model is None:
        return None
    try:
        vecs = model.encode([text_a, text_b], normalize_embeddings=True)
        sim = float(np.dot(vecs[0], vecs[1]))
        return max(0.0, min(1.0, sim))
    except Exception:
        return None


def get_embeddings_batch(texts: list[str]) -> np.ndarray | None:
    """Return an (N, 384) array of normalized embeddings, or None if unavailable.

    Args:
        texts: List of N strings to encode.

    Returns:
        numpy array of shape (N, 384) or None.
    """
    model = load_embedding_model()
    if model is None or not texts:
        return None
    try:
        return model.encode(texts, normalize_embeddings=True)
    except Exception:
        return None
