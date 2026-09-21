"""
core/auth.py — Meridian Match Authentication

Handles SHA-256 password hashing, user credential verification, and account registration.
In production, passwords should use bcrypt or argon2 with per-user cryptographic salts.
"""

from __future__ import annotations

import hashlib
import sqlite3
from core.database import (
    get_user_by_username,
    insert_user,
    insert_blank_client,
    insert_blank_supplier,
    update_user_linked_id,
)


def hash_password(password: str) -> str:
    """Hash a plain-text password using SHA-256 (production requires salted bcrypt)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a plain-text password against a stored SHA-256 hash."""
    return hash_password(plain) == hashed


def login(username: str, password: str) -> sqlite3.Row | None:
    """Verify credentials and return user row if valid, None otherwise."""
    user = get_user_by_username(username)
    if user is None or not verify_password(password, user["password_hash"]):
        return None
    return user


def signup(username: str, password: str, role: str) -> tuple[bool, str, int | None]:
    """
    Register a new user account and auto-create an associated profile row
    in clients or suppliers with profile_complete = False (0).
    """
    uname = username.strip()
    if not uname:
        return False, "Username cannot be empty.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None
    if role not in ("client", "supplier"):
        return False, "Invalid account role.", None

    if get_user_by_username(uname) is not None:
        return False, f"Username '{uname}' is already taken.", None

    pw_hash = hash_password(password)
    try:
        user_id = insert_user(uname, pw_hash, role)

        # Auto-create profile row with profile_complete = False until form is filled
        if role == "client":
            linked_id = insert_blank_client(user_id=user_id, company_name=uname)
        else:
            linked_id = insert_blank_supplier(user_id=user_id, supplier_name=uname)

        update_user_linked_id(user_id, linked_id)
        return True, "Account created successfully!", user_id
    except Exception as exc:
        return False, f"Registration failed: {exc}", None


def username_exists(username: str) -> bool:
    """Check whether a username is already taken."""
    return get_user_by_username(username.strip()) is not None
