# expiry-notifier.py — Password expiry warnings before the lockout tickets

## What it does

Reads a list of users with their last password-change dates, computes how many
days each password has left under your max-age policy (default 90 days), and
emails a heads-up at 14, 7, 3, and 1 day before expiry. Already-expired
accounts are flagged separately so you can prioritize them.

## Why a helpdesk tech wants it

Expired passwords and surprise morning lockouts are one of the most common
tier-1 ticket categories — and every single one is preventable. A scheduled
run of this script turns "I can't log in" firefighting into a polite email the
user got two weeks ago.

## Requirements

- Python 3.8+ (standard library only — `csv`, `smtplib`, `datetime`, `email`)
- Any OS (it never touches the local machine — it just reads the CSV and sends mail)
- An SMTP server you can send through (Gmail/Outlook app password, internal relay, etc.)

## Step-by-step usage

**1. Get the files** — copy `expiry-notifier.py` and the sample `users.csv` to
any machine with Python.

**2. Prepare your user list** — a CSV with this header row (dates in
`YYYY-MM-DD`):

```csv
username,email,last_password_change
agarcia,agarcia@example.com,2026-07-28
bpatel,bpatel@example.com,2026-07-21
```

**3. Dry-run first** (default — sends nothing, just shows the plan):

```bash
python expiry-notifier.py --users users.csv
```

Realistic example output:

```
Checked 6 users against a 90-day policy (today: 2026-10-12).

EXPIRED (1) — already locked out or about to be:
  ekim <ekim@example.com> expired 5d ago

TO WARN (4):
  agarcia <agarcia@example.com> — 14d left
  bpatel <bpatel@example.com> — 7d left
  cnguyen <cnguyen@example.com> — 3d left
  dlee <dlee@example.com> — 1d left

DRY RUN — no emails sent. Re-run with --send to send for real.
```

**4. Send for real** — only when the dry-run looks right:

```bash
python expiry-notifier.py --users users.csv --send \
    --smtp-host smtp.gmail.com --smtp-port 587 \
    --smtp-user notifier@example.com --smtp-pass 'your-app-password'
```

**5. Schedule it** — run the dry-run command daily via Windows Task Scheduler
or cron; add `--send` once you trust the list. One run per day is plenty
(warnings only fire on exact threshold days, so nobody gets spammed).

### Useful variations

```bash
python expiry-notifier.py --users users.csv --max-age 60        # 60-day policy
python expiry-notifier.py --users users.csv --thresholds 30,7  # custom warning days
```

## Safety notes

- **Dry-run is the default.** The script prints exactly who would be emailed
  and refuses to send unless you pass `--send` explicitly.
- Even in `--send` mode it prints the full plan first, then sends.
- SMTP credentials go on the command line — in production, read them from
  environment variables or a secrets store instead of shell history.
- Always sends over STARTTLS when the server supports it (`--no-tls` exists
  only for local test relays).

## Production path: Active Directory integration

The CSV is a stand-in so the script runs anywhere with zero setup. In a real
environment, replace `load_users()` with a direct Active Directory read — the
rest of the logic (thresholds, messages, sending) doesn't change:

1. Install `ldap3` (`pip install ldap3`) — the one external dependency this
   design point needs.
2. Bind to your domain controller and search for user objects, reading the
   `pwdLastSet` attribute (a Windows FILETIME timestamp).
3. Convert FILETIME → datetime: `(pwdLastSet / 10_000_000) - 11644473600`
   gives Unix epoch seconds; `datetime.fromtimestamp()` the rest.
4. Feed those `(username, email, last_change)` tuples into the existing
   pipeline where the CSV rows go today.

That swap is ~30 lines. The scheduling story stays the same: one Task
Scheduler job per day, running as a service account with read access to AD.
