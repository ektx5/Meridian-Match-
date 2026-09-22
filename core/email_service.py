"""
core/email_service.py — Meridian Match Email Notification Service

Sends match notification emails via SMTP_SSL using environment variables.
If any required env variable is missing, logs to console and returns False
(demo-safe — no crash, no configuration required in development).

Required environment variables (set in .env or shell):
    SMTP_HOST  — e.g. smtp.gmail.com
    SMTP_PORT  — e.g. 465
    SMTP_USER  — your sender email address
    SMTP_PASS  — your app password
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.text import MIMEText


def send_match_email(
    to_email: str,
    role: str,
    match_score: float,
    partner_name: str,
    explanation: str,
    top_terms: str | None = None,
) -> bool:
    """Send a match notification email.

    Reads SMTP config from environment variables.  Returns False gracefully
    if any config is missing (demo mode) or if sending fails.

    Args:
        to_email:     Recipient email address.
        role:         'client' or 'supplier' (affects email copy).
        match_score:  Overall match score (0–100).
        partner_name: The matched client or supplier name.
        explanation:  Plain-English match summary sentence.
        top_terms:    Optional comma-joined key shared terms.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port_str = os.environ.get("SMTP_PORT", "465")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not all([smtp_host, smtp_user, smtp_pass]):
        print(
            f"[email_service] Demo mode — SMTP not configured. "
            f"Would have emailed {to_email}: match with {partner_name} ({match_score:.0f}%)"
        )
        return False

    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 465

    if role == "client":
        context_line = "A supplier has been matched with your product requirement."
    else:
        context_line = "A client requirement matches your product offering."

    terms_line = f"\nKey shared terms: {top_terms}" if top_terms else ""

    body = (
        f"Hello,\n\n"
        f"{context_line}\n\n"
        f"Match Partner : {partner_name}\n"
        f"Match Score   : {match_score:.0f}%\n"
        f"Summary       : {explanation}{terms_line}\n\n"
        f"Log in to Meridian Match to view the full breakdown and take action.\n\n"
        f"— The Meridian Match Team"
    )

    subject = f"Meridian Match — New Match: {partner_name} ({match_score:.0f}%)"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        return True
    except Exception as exc:
        print(f"[email_service] Send failed: {exc}")
        return False
