#!/usr/bin/env python3
"""
printer-reset.py — Print spooler rescue for stuck print queues.

Why this exists: "the printer isn't working" is a daily tier-1 ticket, and
half the time the fix is the same ritual — stop the Print Spooler service,
delete the stuck jobs in the spool folder, restart the service. This script
does the ritual in one command so every tech does it the same way, every time.

WINDOWS ONLY. Exits with a clear message on any other OS.

Safety model: --dry-run is the default and only LISTS what would happen.
Nothing touches the system unless you pass --yes. Stopping/starting services
and deleting spool files needs an administrator command prompt.

Usage:
    python printer-reset.py              # dry run: show the plan, change nothing
    python printer-reset.py --yes        # do it for real
    python printer-reset.py --yes --test-page  # also print a test page after
"""

import argparse
import ctypes
import datetime
import os
import shutil
import subprocess
import sys

SERVICE = "spooler"


def log(msg):
    """Timestamped log line — the audit trail for the ticket."""
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {msg}")


def is_admin():
    """True if running elevated. Spooler control needs admin rights."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def spool_dir():
    windir = os.environ.get("WINDIR", r"C:\Windows")
    return os.path.join(windir, "System32", "spool", "PRINTERS")


def list_spool_files():
    """Files currently stuck in the spool folder (the jobs we'll delete)."""
    d = spool_dir()
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d)
            if os.path.isfile(os.path.join(d, f))]


def default_printer():
    """Name of the default printer, or None if we can't determine it."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Printer | Where-Object {$_.IsDefault}).Name"],
            capture_output=True, text=True, timeout=20).stdout.strip()
        return out or None
    except Exception:
        return None


def run_step(description, command):
    """Execute one step, logging success/failure. Returns True on success."""
    log(f">>> {description}")
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=60)
        if result.returncode == 0:
            log("    OK")
            return True
        log(f"    FAILED (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}")
        return False
    except Exception as e:  # e.g. command not found
        log(f"    FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Rescue stuck print queues: restart the Print Spooler "
                    "and clear its spool folder. Dry-run by default.")
    parser.add_argument("--yes", action="store_true",
                        help="Actually perform the reset (default is dry-run)")
    parser.add_argument("--test-page", action="store_true",
                        help="Print a Windows test page on the default printer "
                             "after the reset (only with --yes)")
    args = parser.parse_args()

    if sys.platform != "win32":
        # Clean refusal: this tool is meaningless anywhere else, and saying
        # so beats a confusing traceback. (--help still works everywhere
        # because argparse handles it before we get here.)
        sys.exit("printer-reset.py is Windows-only (it controls the Windows "
                 "Print Spooler service). Nothing was changed.")

    if not is_admin():
        print("WARNING: you don't appear to be running as Administrator. "
              "Stopping/starting the spooler service will likely fail.\n"
              "Re-run from an elevated command prompt for the real fix.\n")

    stuck = list_spool_files()
    printer = default_printer() if args.test_page else None

    # --- The plan, built first so dry-run and real mode show the same steps.
    plan = [
        ("Stop the Print Spooler service",
         ["net", "stop", SERVICE]),
        (f"Delete {len(stuck)} stuck job file(s) from {spool_dir()}",
         None),  # file deletion, handled specially below
        ("Start the Print Spooler service",
         ["net", "start", SERVICE]),
    ]
    if args.test_page:
        if printer:
            plan.append(
                (f"Print a test page on '{printer}'",
                 ["rundll32", "printui.dll,PrintUIEntry",
                  "/k", "/n", printer]))
        else:
            plan.append(("Print a test page — SKIPPED, no default printer found",
                         None))

    print("=== Print spooler rescue plan ===\n")
    for i, (desc, _) in enumerate(plan, 1):
        print(f"  {i}. {desc}")
    if stuck:
        for f in stuck:
            print(f"       - {f}")
    print()

    if not args.yes:
        print("DRY RUN — nothing was changed. Re-run with --yes to execute.")
        return

    # --- Real mode. ---
    log("Starting spooler reset (--yes confirmed)")
    ok = True

    ok &= run_step("Stopping Print Spooler", ["net", "stop", SERVICE])

    log(f"Deleting {len(stuck)} file(s) from spool folder")
    for f in stuck:
        try:
            os.remove(f)
            log(f"    deleted {f}")
        except Exception as e:
            log(f"    FAILED to delete {f}: {e}")
            ok = False
    if not stuck:
        log("    (spool folder already empty)")

    ok &= run_step("Starting Print Spooler", ["net", "start", SERVICE])

    if args.test_page and printer:
        ok &= run_step(f"Printing test page on '{printer}'",
                       ["rundll32", "printui.dll,PrintUIEntry",
                        "/k", "/n", printer])

    print()
    if ok:
        log("Spooler reset complete. If printing still fails, the problem is "
            "upstream (driver, network, or the printer itself) — escalate "
            "with the log above attached to the ticket.")
    else:
        log("Spooler reset finished WITH ERRORS — see FAILED lines above. "
            "Common cause: not running as Administrator.")


if __name__ == "__main__":
    main()
