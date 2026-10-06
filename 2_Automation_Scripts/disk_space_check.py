"""Disk space check.

Looks at each drive, works out how much space is free, and flags any drive
below a minimum percentage. Results print to the screen and are appended to
disk_check_log.txt.

Usage:  python disk_space_check.py
"""
import os
import platform
import shutil
import string
import sys
from datetime import datetime

MIN_FREE_PERCENT = 15  # flag a drive when less than this much is free
LOG_FILE = "disk_check_log.txt"
GB = 1024 ** 3


def find_drives():
    """Return the list of drives/mount points to check."""
    if platform.system() == "Windows":
        # Try every letter A-Z and keep the ones that exist.
        return [l + ":\\" for l in string.ascii_uppercase if os.path.exists(l + ":\\")]
    return ["/"]


def check_drive(path):
    """Return a dict describing one drive's space and status."""
    usage = shutil.disk_usage(path)
    percent_free = usage.free / usage.total * 100
    return {
        "drive": path,
        "total_gb": usage.total / GB,
        "free_gb": usage.free / GB,
        "percent_free": percent_free,
        "status": "OK" if percent_free >= MIN_FREE_PERCENT else "LOW",
    }


def main():
    lines = ["=== Disk check: %s ===" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    any_low = False
    for drive in find_drives():
        try:
            r = check_drive(drive)
        except OSError as err:
            # Example: an empty card reader or disconnected network drive.
            lines.append("%s  could not be read (%s)" % (drive, err))
            continue
        if r["status"] == "LOW":
            any_low = True
        lines.append(
            "%-5s total %.1f GB | free %.1f GB (%.0f%%) | %s"
            % (r["drive"], r["total_gb"], r["free_gb"], r["percent_free"], r["status"])
        )

    report = "\n".join(lines)
    print(report)
    with open(LOG_FILE, "a") as log:
        log.write(report + "\n\n")
    sys.exit(1 if any_low else 0)


if __name__ == "__main__":
    main()
