#!/usr/bin/env python3
"""
Send the daily digest email via Gmail SMTP.

Usage:
    python tools/send_email.py --subject "..." --html-file path/to/body.html

Required env vars:
    GMAIL_USER          your Gmail address (the From address)
    GMAIL_APP_PASSWORD  a 16-char Google App Password (NOT your regular password)
    EMAIL_TO            where the digest goes (can equal GMAIL_USER)

How to get an App Password:
    1. Enable 2-step verification on your Google account.
    2. Visit https://myaccount.google.com/apppasswords
    3. Create an app password for 'Mail'. Copy the 16-character code.
    4. Put it in your .env as GMAIL_APP_PASSWORD (spaces don't matter).
"""

import argparse
import os
import smtplib
import sys
from email.message import EmailMessage


def send(subject: str, html_body: str) -> None:
    user = os.environ.get("GMAIL_USER")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("EMAIL_TO")

    missing = [k for k, v in [("GMAIL_USER", user), ("GMAIL_APP_PASSWORD", pw), ("EMAIL_TO", to)] if not v]
    if missing:
        raise SystemExit(f"missing env vars: {', '.join(missing)}")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.set_content("This email is HTML — your client doesn't seem to be rendering it.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, pw.replace(" ", ""))
        smtp.send_message(msg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--html-file", required=True, help="Path to an HTML file with the email body")
    args = ap.parse_args()

    with open(args.html_file, "r", encoding="utf-8") as f:
        body = f.read()

    try:
        send(args.subject, body)
    except Exception as e:  # noqa: BLE001
        print(f"send failed: {e}", file=sys.stderr)
        return 1

    print("sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
