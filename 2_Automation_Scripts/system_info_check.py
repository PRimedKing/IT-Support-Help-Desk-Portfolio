"""System information check.

Collects basic facts about this computer and compares them to expected values.
Results print to the screen and are appended to system_check_log.txt.

Usage:  python system_info_check.py
"""
import platform
import socket
import sys
from datetime import datetime

# Expected values. Change these to match what your environment requires.
MIN_PYTHON = (3, 8)
SUPPORTED_SYSTEMS = {"Windows", "Darwin", "Linux"}  # Darwin = macOS
LOG_FILE = "system_check_log.txt"


def collect_info():
    """Return a dictionary of basic system facts."""
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "unknown",
        "python_version": platform.python_version(),
    }


def check_info(info):
    """Compare collected values to the expected values above.

    Returns a list of (check name, passed, detail) tuples.
    """
    results = []
    results.append(("OS is supported", info["os"] in SUPPORTED_SYSTEMS, info["os"]))
    py_ok = sys.version_info >= MIN_PYTHON
    results.append(
        ("Python >= %d.%d" % MIN_PYTHON, py_ok, info["python_version"])
    )
    return results


def main():
    info = collect_info()
    results = check_info(info)

    lines = ["=== System check: %s ===" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    for key, value in info.items():
        lines.append("%-15s %s" % (key + ":", value))
    lines.append("")
    for name, passed, detail in results:
        lines.append("[%s] %s (%s)" % ("PASS" if passed else "FAIL", name, detail))

    report = "\n".join(lines)
    print(report)
    with open(LOG_FILE, "a") as log:
        log.write(report + "\n\n")

    # Exit code 1 tells other tools or scripts that something failed.
    sys.exit(0 if all(passed for _, passed, _ in results) else 1)


if __name__ == "__main__":
    main()
