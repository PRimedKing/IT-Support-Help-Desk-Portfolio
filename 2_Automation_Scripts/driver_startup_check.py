"""Driver and startup check (Windows only).

1. Lists drivers that are NOT digitally signed. Unsigned drivers are a common
   cause of crashes and can be a security concern.
2. Counts startup programs and warns if there are a lot, since too many
   slow down boot time.

Usage:  python driver_startup_check.py
"""
import csv
import io
import platform
import subprocess
import sys

MAX_STARTUP_ITEMS = 15  # warn above this many startup programs


def run_command(command):
    """Run a command and return its text output (or None if it failed)."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=90
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        print("Could not run %s: %s" % (command[0], err))
        return None
    if result.returncode != 0:
        print("%s returned an error: %s" % (command[0], result.stderr.strip()))
        return None
    return result.stdout


def parse_unsigned_drivers(csv_text):
    """Return device names of drivers whose IsSigned column is FALSE."""
    reader = csv.DictReader(io.StringIO(csv_text))
    return [
        row["DeviceName"]
        for row in reader
        if row.get("IsSigned", "").strip().upper() == "FALSE"
    ]


def parse_startup_items(csv_text):
    """Return a list of (name, command) for each startup program."""
    reader = csv.DictReader(io.StringIO(csv_text))
    return [(row["Name"], row["Command"]) for row in reader]


def main():
    if platform.system() != "Windows":
        print("This script only works on Windows.")
        sys.exit(2)

    problems = 0

    # --- Drivers ---
    # driverquery /si shows signing info; /fo csv makes the output easy to parse.
    drivers_out = run_command(["driverquery", "/si", "/fo", "csv"])
    if drivers_out:
        unsigned = parse_unsigned_drivers(drivers_out)
        if unsigned:
            problems += 1
            print("[WARN] %d unsigned driver(s):" % len(unsigned))
            for name in unsigned:
                print("   - " + name)
        else:
            print("[PASS] All listed drivers are signed.")

    # --- Startup items ---
    startup_out = run_command(
        [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_StartupCommand | "
            "Select-Object Name, Command | ConvertTo-Csv -NoTypeInformation",
        ]
    )
    if startup_out:
        items = parse_startup_items(startup_out)
        if len(items) > MAX_STARTUP_ITEMS:
            problems += 1
            print("[WARN] %d startup items (limit %d):" % (len(items), MAX_STARTUP_ITEMS))
        else:
            print("[PASS] %d startup items (limit %d):" % (len(items), MAX_STARTUP_ITEMS))
        for name, command in items:
            print("   - %s" % name)

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
