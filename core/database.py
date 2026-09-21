"""
core/database.py — Meridian Match Database Layer

All operations use parameterized queries on raw sqlite3 (no ORM).
Supports client/supplier profiles, matching records, and notifications.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE_DIR, "bridge_bloom.db")
SCHEMA_PATH = os.path.join(_BASE_DIR, "schema.sql")


def get_connection() -> sqlite3.Connection:
    """Return an active SQLite connection configured with Row factory and WAL mode."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize database tables from schema.sql if not present."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        sql = fh.read()
    conn = get_connection()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


# ── Users ──────────────────────────────────────────────────────────────────────

def insert_user(username: str, password_hash: str, role: str, linked_id: int | None = None) -> int:
    """Insert a new user account with hashed password and role ('client'|'supplier'|'admin')."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role, linked_id) VALUES (?,?,?,?)",
            (username, password_hash, role, linked_id),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def get_user_by_username(username: str) -> sqlite3.Row | None:
    """Fetch user account by username."""
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    finally:
        conn.close()


def update_user_linked_id(user_id: int, linked_id: int) -> None:
    """Link a user to their corresponding client or supplier profile record."""
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET linked_id = ? WHERE id = ?", (linked_id, user_id))
        conn.commit()
    finally:
        conn.close()


# ── Clients ────────────────────────────────────────────────────────────────────

def insert_blank_client(user_id: int, company_name: str) -> int:
    """Insert initial incomplete client profile record for a newly signed-up user."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO clients (user_id, company_name, profile_complete) VALUES (?, ?, 0)",
            (user_id, company_name),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def save_or_update_client(
    user_id: int, company_name: str, product_requirement: str, category: str,
    quantity_required: float, quantity_unit: str, budget_min: float, budget_max: float,
    location: str, delivery_days: int, additional_notes: str,
) -> int:
    """Insert or update a client requirement profile and set profile_complete = 1."""
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM clients WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE clients SET company_name=?, product_requirement=?, category=?, quantity_required=?,
                   quantity_unit=?, budget_min=?, budget_max=?, location=?, delivery_days=?, additional_notes=?, profile_complete=1
                   WHERE id=?""",
                (company_name, product_requirement, category, quantity_required, quantity_unit,
                 budget_min, budget_max, location, delivery_days, additional_notes, existing["id"]),
            )
            conn.commit()
            return existing["id"]
        cur = conn.execute(
            """INSERT INTO clients (user_id, company_name, product_requirement, category, quantity_required,
               quantity_unit, budget_min, budget_max, location, delivery_days, additional_notes, profile_complete)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
            (user_id, company_name, product_requirement, category, quantity_required, quantity_unit,
             budget_min, budget_max, location, delivery_days, additional_notes),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def get_client_by_user(user_id: int) -> sqlite3.Row | None:
    """Fetch the latest client requirement profile for a given user id."""
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM clients WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()
    finally:
        conn.close()


def get_all_clients(completed_only: bool = False) -> list[sqlite3.Row]:
    """Return all client profiles, optionally filtering by profile_complete=1."""
    conn = get_connection()
    try:
        sql = "SELECT * FROM clients WHERE profile_complete = 1 ORDER BY id DESC" if completed_only else "SELECT * FROM clients ORDER BY id DESC"
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


# ── Suppliers ──────────────────────────────────────────────────────────────────

def insert_blank_supplier(user_id: int, supplier_name: str) -> int:
    """Insert initial incomplete supplier offering record for a newly signed-up user."""
    conn = get_connection()
    try:
        cur = conn.execute("INSERT INTO suppliers (user_id, supplier_name, profile_complete) VALUES (?, ?, 0)", (user_id, supplier_name))
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def save_or_update_supplier(
    user_id: int, supplier_name: str, product_offered: str, category: str,
    available_quantity: float, quantity_unit: str, price_min: float, price_max: float,
    location: str, delivery_days: int, additional_notes: str,
) -> int:
    """Insert or update a supplier offering profile and set profile_complete = 1."""
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM suppliers WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE suppliers SET supplier_name=?, product_offered=?, category=?, available_quantity=?,
                   quantity_unit=?, price_min=?, price_max=?, location=?, delivery_days=?, additional_notes=?, profile_complete=1
                   WHERE id=?""",
                (supplier_name, product_offered, category, available_quantity, quantity_unit,
                 price_min, price_max, location, delivery_days, additional_notes, existing["id"]),
            )
            conn.commit()
            return existing["id"]
        cur = conn.execute(
            """INSERT INTO suppliers (user_id, supplier_name, product_offered, category, available_quantity,
               quantity_unit, price_min, price_max, location, delivery_days, additional_notes, profile_complete)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
            (user_id, supplier_name, product_offered, category, available_quantity, quantity_unit,
             price_min, price_max, location, delivery_days, additional_notes),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def get_supplier_by_user(user_id: int) -> sqlite3.Row | None:
    """Fetch the latest supplier offering profile for a given user id."""
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM suppliers WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()
    finally:
        conn.close()


def get_all_suppliers(completed_only: bool = False) -> list[sqlite3.Row]:
    """Return all supplier profiles, optionally filtering by profile_complete=1."""
    conn = get_connection()
    try:
        sql = "SELECT * FROM suppliers WHERE profile_complete = 1 ORDER BY id DESC" if completed_only else "SELECT * FROM suppliers ORDER BY id DESC"
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


# ── Matches ────────────────────────────────────────────────────────────────────

def upsert_match(
    client_id: int, supplier_id: int, overall_score: float, product_fit_score: float,
    category_score: float, quantity_score: float, budget_score: float,
    delivery_score: float, location_score: float, constraint_penalty_applied: int,
    explanation_text: str,
) -> int:
    """Insert or update a match record for a client-supplier pair."""
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM matches WHERE client_id=? AND supplier_id=?", (client_id, supplier_id)).fetchone()
        params = (
            overall_score, product_fit_score, category_score, quantity_score, budget_score,
            delivery_score, location_score, constraint_penalty_applied, explanation_text, client_id, supplier_id,
        )
        if existing:
            conn.execute(
                """UPDATE matches SET overall_score=?, product_fit_score=?, category_score=?, quantity_score=?,
                   budget_score=?, delivery_score=?, location_score=?, constraint_penalty_applied=?, explanation_text=?,
                   created_at=CURRENT_TIMESTAMP WHERE client_id=? AND supplier_id=?""", params,
            )
            conn.commit()
            return existing["id"]
        cur = conn.execute(
            """INSERT INTO matches (overall_score, product_fit_score, category_score, quantity_score, budget_score,
               delivery_score, location_score, constraint_penalty_applied, explanation_text, client_id, supplier_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""", params,
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def get_matches_for_client(client_id: int) -> list[sqlite3.Row]:
    """Return all supplier matches for a given client, sorted by score descending."""
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT m.*, s.supplier_name, s.product_offered, s.location AS supplier_location,
                      s.price_min, s.price_max, s.delivery_days AS supplier_delivery,
                      s.available_quantity, s.quantity_unit AS supplier_unit
               FROM matches m JOIN suppliers s ON s.id = m.supplier_id
               WHERE m.client_id = ? ORDER BY m.overall_score DESC""", (client_id,),
        ).fetchall()
    finally:
        conn.close()


def get_matches_for_supplier(supplier_id: int) -> list[sqlite3.Row]:
    """Return all client matches for a given supplier, sorted by score descending."""
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT m.*, c.company_name, c.product_requirement, c.location AS client_location,
                      c.budget_min, c.budget_max, c.delivery_days AS client_delivery,
                      c.quantity_required, c.quantity_unit AS client_unit
               FROM matches m JOIN clients c ON c.id = m.client_id
               WHERE m.supplier_id = ? ORDER BY m.overall_score DESC""", (supplier_id,),
        ).fetchall()
    finally:
        conn.close()


def get_all_matches() -> list[sqlite3.Row]:
    """Return all matches joined with client and supplier company names."""
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT m.*, c.company_name, s.supplier_name, c.category AS client_category
               FROM matches m JOIN clients c ON c.id = m.client_id
               JOIN suppliers s ON s.id = m.supplier_id ORDER BY m.overall_score DESC"""
        ).fetchall()
    finally:
        conn.close()


def update_match_status(match_id: int, status: str) -> None:
    """Update status of a match ('Pending'|'Contacted'|'Confirmed'|'Rejected')."""
    conn = get_connection()
    try:
        conn.execute("UPDATE matches SET status=? WHERE id=?", (status, match_id))
        conn.commit()
    finally:
        conn.close()


# ── Match Explanations ─────────────────────────────────────────────────────────

def insert_match_explanation(match_id: int, constraint_type: str, constraint_text: str, satisfied: bool) -> None:
    """Store an individual parsed constraint satisfaction outcome for a match."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO match_explanations (match_id, constraint_type, constraint_text, satisfied) VALUES (?,?,?,?)",
            (match_id, constraint_type, constraint_text, int(satisfied)),
        )
        conn.commit()
    finally:
        conn.close()


def get_explanations_for_match(match_id: int) -> list[sqlite3.Row]:
    """Retrieve all parsed constraint results for a given match."""
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM match_explanations WHERE match_id=? ORDER BY id", (match_id,)).fetchall()
    finally:
        conn.close()


def delete_explanations_for_match(match_id: int) -> None:
    """Clear existing explanation rows for a match prior to re-saving."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM match_explanations WHERE match_id=?", (match_id,))
        conn.commit()
    finally:
        conn.close()


# ── Stats ──────────────────────────────────────────────────────────────────────

def get_stats() -> dict[str, Any]:
    """Compute aggregate counts, averages, and distributions for the dashboard."""
    conn = get_connection()
    try:
        tot_c = conn.execute("SELECT COUNT(*) FROM clients WHERE profile_complete = 1").fetchone()[0]
        tot_s = conn.execute("SELECT COUNT(*) FROM suppliers WHERE profile_complete = 1").fetchone()[0]
        tot_m = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        avg_row = conn.execute("SELECT AVG(overall_score) FROM matches").fetchone()
        avg_score = round(avg_row[0] or 0.0, 1)

        cats = conn.execute(
            """SELECT c.category, COUNT(*) as cnt FROM matches m
               JOIN clients c ON c.id=m.client_id GROUP BY c.category ORDER BY cnt DESC"""
        ).fetchall()
        matches_per_cat = {r["category"]: r["cnt"] for r in cats}
        scores = [r["overall_score"] for r in conn.execute("SELECT overall_score FROM matches").fetchall()]

        return {
            "total_clients": tot_c, "total_suppliers": tot_s, "total_matches": tot_m,
            "avg_score": avg_score, "matches_per_category": matches_per_cat,
            "score_distribution": scores,
        }
    finally:
        conn.close()
