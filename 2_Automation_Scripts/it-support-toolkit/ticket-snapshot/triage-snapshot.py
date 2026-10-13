#!/usr/bin/env python3
"""
triage-snapshot.py — One-command ticket-ready system snapshot.

Why this exists: tier-1 troubleshooting always starts with the same questions
(hostname? OS? disk full? when did it last reboot? any recent errors?). This
script answers all of them in one shot and prints a clean markdown report you
can paste straight into a ticket — no more "can you check your OS version?"
back-and-forth with the user.

Completely read-only: it only READS system info, never changes anything.
Safe to run on any machine, any time.

Usage:
    python triage-snapshot.py                 # markdown report to stdout
    python triage-snapshot.py --output pc42.md # save report to a file
    python triage-snapshot.py --json          # machine-readable JSON instead
"""

import argparse
import ctypes
import datetime
import getpass
import json
import os
import platform
import shutil
import socket
import subprocess
import sys


# ---------------------------------------------------------------------------
# Individual collectors. Each returns a dict (or string) and NEVER raises:
# if a source is unavailable we record "unknown" and move on. A snapshot
# tool that crashes on a weird machine is worse than useless on a helpdesk.
# ---------------------------------------------------------------------------

def safe(fn, fallback="unknown"):
    """Run fn(); on any error return fallback instead of crashing."""
    try:
        return fn()
    except Exception:
        return fallback


def get_hostname():
    return safe(socket.gethostname)


def get_os():
    def _os():
        sys_name = platform.system()
        if sys_name == "Windows":
            # e.g. "Windows 10 (10.0.19045)"
            return f"Windows {platform.release()} ({platform.version()})"
        if sys_name == "Darwin":
            return f"macOS {platform.mac_ver()[0]}"
        return f"{sys_name} {platform.release()}"
    return safe(_os)


def get_user():
    return safe(getpass.getuser)


def get_cpu_count():
    return safe(lambda: str(os.cpu_count() or "unknown"))


def get_memory():
    """Total / available RAM. Needs per-OS handling since stdlib has no API."""
    def _windows():
        # GlobalMemoryStatusEx via ctypes — no subprocess, no dependencies.
        class MemStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        st = MemStatus()
        st.dwLength = ctypes.sizeof(MemStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        gb = 1024 ** 3
        return (f"{st.ullTotalPhys / gb:.1f} GB total, "
                f"{st.ullAvailPhys / gb:.1f} GB available "
                f"({st.dwMemoryLoad}% in use)")

    def _linux():
        # /proc/meminfo is always there on Linux; values are in kB.
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    info[parts[0].rstrip(":")] = int(parts[1])
        total = info.get("MemTotal", 0) / 1024 ** 2
        avail = info.get("MemAvailable", info.get("MemFree", 0)) / 1024 ** 2
        pct = int(100 * (1 - avail / total)) if total else 0
        return f"{total:.1f} GB total, {avail:.1f} GB available ({pct}% in use)"

    def _macos():
        out = subprocess.run(["sysctl", "-n", "hw.memsize"],
                             capture_output=True, text=True, timeout=10)
        total = int(out.stdout.strip()) / 1024 ** 3
        return f"{total:.1f} GB total (per-process breakdown needs Activity Monitor)"

    sys_name = platform.system()
    if sys_name == "Windows":
        return safe(_windows)
    if sys_name == "Linux":
        return safe(_linux)
    if sys_name == "Darwin":
        return safe(_macos)
    return "unknown"


def get_disk():
    def _disk():
        total, used, free = shutil.disk_usage(os.path.abspath(os.sep))
        gb = 1024 ** 3
        pct = int(100 * used / total) if total else 0
        # A nearly-full system drive is one of the most common "my PC is slow"
        # root causes, so flag it loudly in the report.
        flag = "  <-- DISK NEARLY FULL" if pct >= 90 else ""
        return (f"{used / gb:.1f} GB used of {total / gb:.1f} GB "
                f"({pct}% full, {free / gb:.1f} GB free){flag}")
    return safe(_disk)


def get_local_ip():
    def _ip():
        # Opening a UDP socket doesn't send traffic; it just reveals which
        # local interface the OS would route through — the reliable way to
        # get the "real" LAN IP instead of 127.0.0.1.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    return safe(_ip)


def get_gateway():
    def _windows():
        out = subprocess.run(["ipconfig"], capture_output=True, text=True,
                             timeout=15).stdout
        for line in out.splitlines():
            if "Default Gateway" in line and ":" in line:
                gw = line.split(":")[-1].strip()
                if gw:
                    return gw
        return "unknown"

    def _linux():
        out = subprocess.run(["ip", "route", "show", "default"],
                             capture_output=True, text=True,
                             timeout=10).stdout
        parts = out.split()
        if "via" in parts:
            return parts[parts.index("via") + 1]
        return "unknown"

    def _macos():
        out = subprocess.run(["route", "-n", "get", "default"],
                             capture_output=True, text=True,
                             timeout=10).stdout
        for line in out.splitlines():
            if "gateway:" in line:
                return line.split("gateway:")[1].strip()
        return "unknown"

    sys_name = platform.system()
    if sys_name == "Windows":
        return safe(_windows)
    if sys_name == "Linux":
        return safe(_linux)
    if sys_name == "Darwin":
        return safe(_macos)
    return "unknown"


def get_dns():
    def _windows():
        out = subprocess.run(["nslookup", "localhost"],
                             capture_output=True, text=True,
                             timeout=15).stdout
        for line in out.splitlines():
            if "Address" in line and ":" in line:
                addr = line.split(":")[-1].strip()
                if addr and not addr.startswith("127."):
                    return addr
        return "unknown"

    def _unix():
        # /etc/resolv.conf lists configured nameservers on Linux and macOS.
        servers = []
        with open("/etc/resolv.conf") as f:
            for line in f:
                if line.startswith("nameserver"):
                    servers.append(line.split()[1])
        return ", ".join(servers) if servers else "unknown"

    if platform.system() == "Windows":
        return safe(_windows)
    return safe(_unix)


def get_uptime():
    def _windows():
        ms = ctypes.windll.kernel32.GetTickCount64()
        return _format_uptime(datetime.timedelta(milliseconds=ms))

    def _linux():
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        return _format_uptime(datetime.timedelta(seconds=seconds))

    def _macos():
        out = subprocess.run(["sysctl", "-n", "kern.boottime"],
                             capture_output=True, text=True, timeout=10)
        # "Tue Oct  7 08:12:33 2026" — boot time; uptime = now - boot.
        boot = datetime.datetime.strptime(out.stdout.strip(),
                                          "%a %b %d %H:%M:%S %Y")
        return _format_uptime(datetime.datetime.now() - boot)

    sys_name = platform.system()
    if sys_name == "Windows":
        return safe(_windows)
    if sys_name == "Linux":
        return safe(_linux)
    if sys_name == "Darwin":
        return safe(_macos)
    return "unknown"


def _format_uptime(delta):
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def get_recent_errors(count=5):
    """Last few system errors. Windows: real Event Log via wevtutil.
    Elsewhere: honest 'not available' — faking it would be worse."""
    if platform.system() != "Windows":
        return ["(event-log collection is Windows-only; "
                "check /var/log on Linux/macOS)"]

    def _errors():
        # wevtutil ships with every Windows install; no extra tools needed.
        # Level=2 means Error (1=Critical, 3=Warning).
        result = subprocess.run(
            ["wevtutil", "qe", "System", f"/c:{count}",
             "/rd:true", "/f:text",
             "/q:*[System[(Level=2)]]"],
            capture_output=True, text=True, timeout=30)
        events, current = [], []
        for line in result.stdout.splitlines():
            if line.startswith("Event["):
                if current:
                    events.append(" | ".join(current))
                current = []
            elif line.strip().startswith(("Date:", "Source:", "Description:")):
                current.append(line.strip())
        if current:
            events.append(" | ".join(current))
        return events if events else ["(no recent system errors found)"]
    return safe(_errors, fallback=["(could not read event log)"])


def collect():
    """Gather everything into one ordered dict for the report."""
    return {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "hostname": get_hostname(),
        "os": get_os(),
        "logged_in_user": get_user(),
        "cpu_cores": get_cpu_count(),
        "memory": get_memory(),
        "disk_system_drive": get_disk(),
        "local_ip": get_local_ip(),
        "default_gateway": get_gateway(),
        "dns_server": get_dns(),
        "uptime": get_uptime(),
        "recent_system_errors": get_recent_errors(),
    }


def to_markdown(d):
    lines = [
        "# System Snapshot",
        f"_Generated {d['generated_at']} on {d['hostname']}_",
        "",
        "| Item | Value |",
        "| ---- | ----- |",
        f"| Hostname | {d['hostname']} |",
        f"| OS | {d['os']} |",
        f"| Logged-in user | {d['logged_in_user']} |",
        f"| CPU cores | {d['cpu_cores']} |",
        f"| Memory | {d['memory']} |",
        f"| Disk (system drive) | {d['disk_system_drive']} |",
        f"| Local IP | {d['local_ip']} |",
        f"| Default gateway | {d['default_gateway']} |",
        f"| DNS server | {d['dns_server']} |",
        f"| Uptime | {d['uptime']} |",
        "",
        "## Recent system errors",
        "",
    ]
    for e in d["recent_system_errors"]:
        lines.append(f"- {e}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Collect a ticket-ready system snapshot (read-only).")
    parser.add_argument("--output", metavar="FILE",
                        help="Write the markdown report to FILE instead of stdout")
    parser.add_argument("--json", action="store_true",
                        help="Output machine-readable JSON instead of markdown")
    args = parser.parse_args()

    data = collect()

    if args.json:
        text = json.dumps(data, indent=2)
    else:
        text = to_markdown(data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Snapshot written to {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
