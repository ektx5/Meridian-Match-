"""
core/notifications.py — Meridian Match Notification System

Handles creation, retrieval, and mark-as-read operations for notifications.
Notifications are generated automatically when a match score exceeds 60.
"""

import sqlite3
from core.database import get_connection

SCORE_THRESHOLD = 60.0


def create_match_notifications(
    client_id: int,
    supplier_id: int,
    match_id: int,
    score: float,
    explanation: str,
    client_user_id: int,
    supplier_user_id: int,
) -> None:
    """
    Create notification rows for both client and supplier when score > threshold.

    Args:
        client_id: The client entity id.
        supplier_id: The supplier entity id.
        match_id: FK to matches.id.
        score: The overall match score (0–100).
        explanation: The plain-English explanation sentence.
        client_user_id: The user account id of the client.
        supplier_user_id: The user account id of the supplier.
    """
    if score < SCORE_THRESHOLD:
        return

    conn = get_connection()
    try:
        client_msg = (
            f"🎉 New match ({score:.0f}%): A supplier has been matched with your requirement. "
            f"{explanation}"
        )
        supplier_msg = (
            f"🎉 New match ({score:.0f}%): A client requirement matches your offering. "
            f"{explanation}"
        )

        # Dedup: only insert if a notification for this user+match doesn't already exist
        existing_c = conn.execute(
            "SELECT id FROM notifications WHERE user_id=? AND match_id=? AND user_role='client'",
            (client_user_id, match_id),
        ).fetchone()
        if not existing_c:
            conn.execute(
                """INSERT INTO notifications (user_role, user_id, match_id, message)
                   VALUES ('client', ?, ?, ?)""",
                (client_user_id, match_id, client_msg),
            )

        existing_s = conn.execute(
            "SELECT id FROM notifications WHERE user_id=? AND match_id=? AND user_role='supplier'",
            (supplier_user_id, match_id),
        ).fetchone()
        if not existing_s:
            conn.execute(
                """INSERT INTO notifications (user_role, user_id, match_id, message)
                   VALUES ('supplier', ?, ?, ?)""",
                (supplier_user_id, match_id, supplier_msg),
            )
        conn.commit()
    finally:
        conn.close()


def get_notifications_for_user(
    user_id: int, role: str, limit: int = 20
) -> list[sqlite3.Row]:
    """
    Fetch recent notifications for a user, newest first.

    Args:
        user_id: The user's id.
        role: 'client' or 'supplier'.
        limit: Maximum number of rows to return.

    Returns:
        List of sqlite3.Row objects.
    """
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT * FROM notifications
               WHERE user_id = ? AND user_role = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, role, limit),
        ).fetchall()
    finally:
        conn.close()


def get_unread_count(user_id: int, role: str) -> int:
    """
    Return the count of unread notifications for a user.

    Args:
        user_id: The user's id.
        role: 'client' or 'supplier'.

    Returns:
        Integer count of unread notification rows.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT COUNT(*) FROM notifications
               WHERE user_id = ? AND user_role = ? AND is_read = 0""",
            (user_id, role),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def mark_notification_read(notification_id: int) -> None:
    """
    Mark a single notification as read.

    Args:
        notification_id: The notification's primary key id.
    """
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,),
        )
        conn.commit()
    finally:
        conn.close()


def mark_all_read(user_id: int, role: str) -> None:
    """
    Mark all notifications as read for a given user.

    Args:
        user_id: The user's id.
        role: 'client' or 'supplier'.
    """
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE notifications SET is_read = 1
               WHERE user_id = ? AND user_role = ?""",
            (user_id, role),
        )
        conn.commit()
    finally:
        conn.close()


def create_notifications_for_matches(match_results: list[dict], client_row, supplier_rows: dict) -> None:
    """
    Bulk-create notifications for a list of match results (used after seeding or re-run).

    Args:
        match_results: List of match result dicts from the matching engine.
        client_row: sqlite3.Row for the client.
        supplier_rows: Dict mapping supplier_id -> sqlite3.Row for suppliers.
    """
    conn = get_connection()
    try:
        for m in match_results:
            if m["overall_score"] < SCORE_THRESHOLD:
                continue
            supplier = supplier_rows.get(m.get("supplier_id"))
            if supplier is None:
                continue

            # Look up user ids
            c_user = conn.execute(
                "SELECT id FROM users WHERE linked_id = ? AND role = 'client'",
                (client_row["id"],),
            ).fetchone()
            s_user = conn.execute(
                "SELECT id FROM users WHERE linked_id = ? AND role = 'supplier'",
                (supplier["id"],),
            ).fetchone()

            if c_user is None or s_user is None:
                continue

            score = m["overall_score"]
            explanation = m.get("explanation_text", "")
            match_id = m.get("match_id")

            client_msg = (
                f"🎉 New match ({score:.0f}%): A supplier matches your requirement. "
                f"{explanation}"
            )
            supplier_msg = (
                f"🎉 New match ({score:.0f}%): A client requirement matches your offering. "
                f"{explanation}"
            )

            # Avoid duplicate notifications
            existing_c = conn.execute(
                "SELECT id FROM notifications WHERE user_id=? AND match_id=? AND user_role='client'",
                (c_user["id"], match_id),
            ).fetchone()
            if not existing_c:
                conn.execute(
                    """INSERT INTO notifications (user_role, user_id, match_id, message)
                       VALUES ('client', ?, ?, ?)""",
                    (c_user["id"], match_id, client_msg),
                )

            existing_s = conn.execute(
                "SELECT id FROM notifications WHERE user_id=? AND match_id=? AND user_role='supplier'",
                (s_user["id"], match_id),
            ).fetchone()
            if not existing_s:
                conn.execute(
                    """INSERT INTO notifications (user_role, user_id, match_id, message)
                       VALUES ('supplier', ?, ?, ?)""",
                    (s_user["id"], match_id, supplier_msg),
                )

        conn.commit()
    finally:
        conn.close()
