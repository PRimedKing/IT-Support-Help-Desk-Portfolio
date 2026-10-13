#!/usr/bin/env python3
"""
expiry-notifier.py — Warn users before their passwords expire.

Why this exists: expired passwords and surprise lockouts are one of the most
common tier-1 ticket categories, and every one of them is preventable. This
script reads a list of users with their last password-change dates, figures
out whose passwords are about to expire, and emails them a heads-up at
configurable warning thresholds (default: 14, 7, 3, and 1 day out).

SAFE BY DEFAULT: without --send it only prints who WOULD be emailed
(--dry-run). Nothing is ever sent unless you explicitly ask.

Usage:
    python expiry-notifier.py --users users.csv                  # dry run (default)
    python expiry-notifier.py --users users.csv --max-age 60      # 60-day policy
    python expiry-notifier.py --users users.csv --send \
        --smtp-host mail.example.com --smtp-port 587 \
        --smtp-user notifier@example.com --smtp-pass 'secret'    # actually send

CSV format (header row required):
    username,email,last_password_change
    jsmith,jsmith@example.com,2026-08-01
    (dates in YYYY-MM-DD)

Real-world note: in production this same logic reads from Active Directory
instead of a CSV — see README.md for the integration path.
"""

import argparse
import csv
import datetime
import smtplib
import sys
from email.message import EmailMessage

# Days-before-expiry at which a warning goes out. Only exact matches trigger,
# so a user gets at most one email per threshold (no daily spam).
DEFAULT_THRESHOLDS = [14, 7, 3, 1]


def parse_date(text):
    """Parse YYYY-MM-DD; raise a clear error naming the bad value."""
    try:
        return datetime.date.fromisoformat(text.strip())
    except ValueError:
        raise ValueError(f"bad date '{text}' — expected YYYY-MM-DD")


def load_users(path):
    """Read the CSV into a list of dicts. Fails fast on a bad file."""
    users = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"username", "email", "last_password_change"}
        if not required.issubset(set(reader.fieldnames or [])):
            sys.exit(f"ERROR: CSV must have columns: {sorted(required)} "
                     f"(found: {reader.fieldnames})")
        for lineno, row in enumerate(reader, start=2):
            if not row["username"].strip():
                continue  # skip blank rows quietly
            try:
                row["last_change"] = parse_date(row["last_password_change"])
            except ValueError as e:
                sys.exit(f"ERROR in {path} line {lineno}: {e}")
            users.append(row)
    return users


def days_until_expiry(last_change, max_age_days, today):
    """Whole days left before the password expires (negative = expired)."""
    expiry = last_change + datetime.timedelta(days=max_age_days)
    return (expiry - today).days


def build_message(user, days_left, max_age_days):
    """The warning email. Plain text, actionable, no jargon."""
    msg = EmailMessage()
    if days_left < 0:
        msg["Subject"] = "Action needed: your password has expired"
    else:
        msg["Subject"] = (f"Action needed: your password expires in "
                          f"{days_left} day{'s' if days_left != 1 else ''}")
    msg["From"] = "IT Support <it-support@example.com>"
    msg["To"] = user["email"]
    if days_left < 0:
        body = (f"Hi {user['username']},\n\n"
                f"Your password has EXPIRED. Please reset it now to avoid "
                f"being locked out of your account.\n\n"
                f"— IT Support")
    else:
        body = (f"Hi {user['username']},\n\n"
                f"Your password expires in {days_left} day"
                f"{'s' if days_left != 1 else ''}. Please change it at your "
                f"convenience before then to avoid a lockout.\n\n"
                f"(Passwords expire every {max_age_days} days per company "
                f"policy.)\n\n— IT Support")
    msg.set_content(body)
    return msg


def send_all(warnings, smtp_host, smtp_port, smtp_user, smtp_pass, use_tls=True):
    """Send every prepared message over one SMTP connection."""
    sent = 0
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        if use_tls:
            server.starttls()  # encrypt before the password goes over the wire
        if smtp_user:
            server.login(smtp_user, smtp_pass)
        for user, days_left, max_age, msg in warnings:
            server.send_message(msg)
            sent += 1
            print(f"  SENT to {user['email']} ({days_left}d left)")
    return sent


def main():
    parser = argparse.ArgumentParser(
        description="Email users before their passwords expire. "
                    "Dry-run by default; nothing is sent without --send.")
    parser.add_argument("--users", required=True, metavar="CSV",
                        help="CSV with username,email,last_password_change columns")
    parser.add_argument("--max-age", type=int, default=90, metavar="DAYS",
                        help="Password max age in days (default: 90)")
    parser.add_argument("--thresholds", default=",".join(map(str, DEFAULT_THRESHOLDS)),
                        metavar="N,N,..",
                        help=f"Warn at these days-before-expiry (default: "
                             f"{','.join(map(str, DEFAULT_THRESHOLDS))})")
    parser.add_argument("--send", action="store_true",
                        help="Actually send the emails (default is dry-run)")
    parser.add_argument("--smtp-host", default="localhost",
                        help="SMTP server hostname")
    parser.add_argument("--smtp-port", type=int, default=587,
                        help="SMTP server port (default: 587)")
    parser.add_argument("--smtp-user", default="",
                        help="SMTP username (empty = no auth)")
    parser.add_argument("--smtp-pass", default="",
                        help="SMTP password (prefer an app password / env var)")
    parser.add_argument("--no-tls", action="store_true",
                        help="Skip STARTTLS (only for local test servers)")
    args = parser.parse_args()

    try:
        thresholds = sorted(int(t) for t in args.thresholds.split(","))
    except ValueError:
        sys.exit("ERROR: --thresholds must be comma-separated integers, e.g. 14,7,3,1")

    users = load_users(args.users)
    today = datetime.date.today()

    warnings, expired, ok = [], [], []
    for user in users:
        days_left = days_until_expiry(user["last_change"], args.max_age, today)
        if days_left < 0:
            expired.append((user, days_left))
        elif days_left in thresholds:
            warnings.append((user, days_left, args.max_age,
                             build_message(user, days_left, args.max_age)))
        else:
            ok.append((user, days_left))

    # --- Report first, act second. Even in --send mode you see the plan. ---
    print(f"Checked {len(users)} users against a {args.max_age}-day policy "
          f"(today: {today}).\n")

    if expired:
        print(f"EXPIRED ({len(expired)}) — already locked out or about to be:")
        for user, days_left in expired:
            print(f"  {user['username']} <{user['email']}> "
                  f"expired {-days_left}d ago")
        print()

    if warnings:
        print(f"TO WARN ({len(warnings)}):")
        for user, days_left, _, _ in warnings:
            print(f"  {user['username']} <{user['email']}> — {days_left}d left")
    else:
        print("TO WARN (0): nobody hits a warning threshold today.")

    if args.send:
        if not warnings:
            print("\nNothing to send.")
            return
        print(f"\nSending via {args.smtp_host}:{args.smtp_port} ...")
        sent = send_all(warnings, args.smtp_host, args.smtp_port,
                        args.smtp_user, args.smtp_pass,
                        use_tls=not args.no_tls)
        print(f"Done: {sent} email(s) sent.")
    else:
        print("\nDRY RUN — no emails sent. Re-run with --send to send for real.")


if __name__ == "__main__":
    main()
