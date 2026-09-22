"""
core/email_service.py — Meridian Match Email Notification Service

Sends match notification emails via SMTP_SSL using environment variables.
Defaults to Gmail SMTP (smtp.gmail.com:465) and sender ekta28045@gmail.com.

Required environment variables (set in .env or shell):
    SMTP_HOST  — defaults to smtp.gmail.com
    SMTP_PORT  — defaults to 465
    SMTP_USER  — defaults to ekta28045@gmail.com
    SMTP_PASS  — your 16-character Google App Password
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.text import MIMEText


def _load_env_file() -> None:
    """Load key-value pairs from .env into os.environ if not already present."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        k = key.strip()
                        v = val.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


# Automatically load .env on import
_load_env_file()


def send_match_email(
    to_email: str,
    role: str,
    match_score: float,
    partner_name: str,
    explanation: str,
    top_terms: str | None = None,
) -> tuple[bool, str]:
    """Send a match notification email.

    Reads SMTP config from environment variables / .env file.
    Sender defaults to ekta28045@gmail.com via smtp.gmail.com.

    Args:
        to_email:     Recipient email address.
        role:         'client' or 'supplier' (affects email copy).
        match_score:  Overall match score (0–100).
        partner_name: The matched client or supplier name.
        explanation:  Plain-English match summary sentence.
        top_terms:    Optional comma-joined key shared terms.

    Returns:
        tuple (success: bool, status_message: str)
    """
    _load_env_file()
    smtp_host = os.environ.get("SMTP_HOST", "").strip() or "smtp.gmail.com"
    smtp_port_str = os.environ.get("SMTP_PORT", "").strip() or "465"
    smtp_user = os.environ.get("SMTP_USER", "").strip() or "ekta28045@gmail.com"
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()

    if not smtp_pass:
        msg = (
            f"Email prepared from {smtp_user} to {to_email}. "
            "To send real emails to your inbox, add your 16-character Gmail App Password in .env (SMTP_PASS=...)."
        )
        print(f"[email_service] {msg}")
        return False, msg

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
        success_msg = f"Email notification successfully sent from {smtp_user} to {to_email}!"
        print(f"[email_service] {success_msg}")
        return True, success_msg
    except smtplib.SMTPAuthenticationError:
        err_msg = (
            f"Gmail SMTP authentication failed for {smtp_user}. "
            "Please check that your 16-character Google App Password in .env is correct."
        )
        print(f"[email_service] {err_msg}")
        return False, err_msg
    except Exception as exc:
        err_msg = f"Failed to send email via {smtp_host}: {exc}"
        print(f"[email_service] {err_msg}")
        return False, err_msg
