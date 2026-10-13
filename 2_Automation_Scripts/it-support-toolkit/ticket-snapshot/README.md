# triage-snapshot.py — Ticket-ready system snapshot

## What it does

Collects the answers to the questions every tier-1 ticket starts with — hostname,
OS version, logged-in user, CPU/RAM/disk usage, IP/gateway/DNS, uptime, and
recent system errors — and prints them as a clean markdown report you can paste
straight into a ticket.

## Why a helpdesk tech wants it

The first 10 minutes of most "my computer is slow / something's broken" tickets
is just information gathering: *What OS are you on? How much disk space is
left? When did you last reboot?* This script answers all of that in one command,
so triage starts with facts instead of a back-and-forth. The disk-full flag
alone catches one of the most common root causes of "slow PC" tickets.

## Requirements

- Python 3.8+ (standard library only — no pip installs)
- Works on Windows, macOS, and Linux
- No admin rights needed — **completely read-only**, it never changes anything

## Step-by-step usage

**1. Get the file** — copy `triage-snapshot.py` to the machine (USB drive,
network share, or remote session all work).

**2. Run it:**

```bash
python triage-snapshot.py
```

**3. Read the output** — paste it into the ticket. Realistic example:

```markdown
# System Snapshot
_Generated 2026-10-12 14:20 on DESKTOP-PC42_

| Item | Value |
| ---- | ----- |
| Hostname | DESKTOP-PC42 |
| OS | Windows 10 (10.0.19045) |
| Logged-in user | jsmith |
| CPU cores | 8 |
| Memory | 16.0 GB total, 4.2 GB available (74% in use) |
| Disk (system drive) | 428.5 GB used of 476.9 GB (90% full, 48.4 GB free)  <-- DISK NEARLY FULL |
| Local IP | 192.168.1.42 |
| Default gateway | 192.168.1.1 |
| DNS server | 192.168.1.1 |
| Uptime | 23d 4h 12m |

## Recent system errors

- Date: 10/12/2026 08:14:02 | Source: Disk | Description: The driver detected a controller error on \Device\Harddisk1\DR1.
- Date: 10/11/2026 17:02:44 | Source: Service Control Manager | Description: The Print Spooler service terminated unexpectedly.
```

From that one report a tech can immediately see: the disk is 90% full (likely
the "slowness"), the machine hasn't rebooted in 23 days, and there's a disk
controller error worth escalating — all before calling the user back.

### Other useful forms

```bash
python triage-snapshot.py --output pc42.md   # save the report to a file
python triage-snapshot.py --json             # machine-readable JSON (for feeding into other tools)
```

## Safety notes

- **Read-only by design.** The script only *reads* system information; there is
  no code path that writes, deletes, or changes anything on the machine.
- On non-Windows systems, recent-error collection is skipped with a note
  (Windows Event Log is read via the built-in `wevtutil` — no extra tools).
- Every collector fails gracefully: if a data source is unavailable, the report
  shows "unknown" for that row instead of crashing.
