#!/usr/bin/env python3
"""
netdiag.py — "The internet is slow" turned into data.

Why this exists: vague network complaints are the hardest tier-1 tickets
because there's nothing to go on. This script runs the standard
connectivity ladder — gateway, DNS, public host, name resolution, TCP
ports, traceroute — and ends with a plain-language PASS/FAIL summary plus
an optional CSV log so you can prove whether "slow" is real and when it
started.

Read-only and non-destructive: it only sends ordinary ping/DNS/TCP traffic,
the same as opening a web page. Safe on any machine.

Usage:
    python netdiag.py                      # full check, summary to stdout
    python netdiag.py --host example.com   # test a specific host's web ports
    python netdiag.py --log results.csv    # also append timestamped results
"""

import argparse
import csv
import datetime
import os
import platform
import re
import shutil
import socket
import subprocess
import sys

SYSTEM = platform.system()  # "Windows", "Linux", or "Darwin"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, timeout):
    """Run a command, return (returncode, stdout). Never raises."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout
    except Exception as e:
        return -1, str(e)


def ping_cmd(host, count=3):
    if SYSTEM == "Windows":
        return ["ping", "-n", str(count), "-w", "2000", host]
    if SYSTEM == "Darwin":
        return ["ping", "-c", str(count), "-W", "2000", host]
    return ["ping", "-c", str(count), "-W", "2", host]


def ping_avg_ms(output):
    """Best-effort average latency parse; None if we can't tell."""
    m = re.search(r"Average = (\d+)ms", output)          # Windows
    if m:
        return f"{m.group(1)} ms avg"
    m = re.search(r"rtt [^=]*= [\d.]+/([\d.]+)/", output)  # Linux
    if m:
        return f"{m.group(1)} ms avg"
    m = re.search(r"round-trip [^=]*= [\d.]+/([\d.]+)/", output)  # macOS
    if m:
        return f"{m.group(1)} ms avg"
    return "reachable"


def get_gateway():
    """Best-effort default gateway; None when we can't determine it."""
    def _w():
        rc, out = run(["ipconfig"], 15)
        for line in out.splitlines():
            if "Default Gateway" in line and ":" in line:
                gw = line.split(":")[-1].strip()
                if gw:
                    return gw
        return None
    def _l():
        rc, out = run(["ip", "route", "show", "default"], 10)
        p = out.split()
        return p[p.index("via") + 1] if "via" in p else None
    def _m():
        rc, out = run(["route", "-n", "get", "default"], 10)
        for line in out.splitlines():
            if "gateway:" in line:
                return line.split("gateway:")[1].strip()
        return None
    try:
        if SYSTEM == "Windows":
            return _w()
        if SYSTEM == "Linux":
            return _l()
        if SYSTEM == "Darwin":
            return _m()
    except Exception:
        pass
    return None


def get_dns_server():
    """Best-effort primary DNS; None when we can't determine it."""
    try:
        if SYSTEM == "Windows":
            rc, out = run(["nslookup", "localhost"], 15)
            for line in out.splitlines():
                if "Address" in line and ":" in line:
                    a = line.split(":")[-1].strip()
                    if a and not a.startswith("127."):
                        return a
            return None
        with open("/etc/resolv.conf") as f:
            for line in f:
                if line.startswith("nameserver"):
                    return line.split()[1]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# The checks. Each returns (name, passed: bool, detail: str).
# ---------------------------------------------------------------------------

def check_ping(name, host):
    if not host:
        return (name, None, "skipped — could not determine address")
    rc, out = run(ping_cmd(host), timeout=30)
    if rc == 0:
        return (name, True, f"{host} — {ping_avg_ms(out)}")
    return (name, False, f"{host} — no reply")


def check_dns(name="DNS resolution"):
    try:
        ip = socket.gethostbyname("www.google.com")
        return (name, True, f"www.google.com -> {ip}")
    except Exception as e:
        return (name, False, f"could not resolve www.google.com ({e})")


def check_tcp_port(host, port, timeout=5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return (f"TCP port {port} on {host}", True, "open")
    except Exception as e:
        return (f"TCP port {port} on {host}", False, f"closed/unreachable ({e})")


def check_traceroute(host):
    tool = "tracert" if SYSTEM == "Windows" else "traceroute"
    if not shutil.which(tool):
        return ("Traceroute", None, f"skipped — '{tool}' not installed")
    cmd = ([tool, "-h", "12", "-w", "1000", host] if SYSTEM == "Windows"
           else [tool, "-m", "12", "-w", "2", host])
    rc, out = run(cmd, timeout=60)
    hops = [l for l in out.splitlines() if l.strip()]
    # Just count responding hops; full output goes in the log detail.
    return ("Traceroute", rc == 0,
            f"{len(hops)} hops recorded to {host}" if rc == 0
            else f"incomplete to {host}")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def summarize(results):
    """Plain-language verdict a non-technical user (or manager) can read."""
    failed = [n for n, ok, _ in results if ok is False]
    if not failed:
        return ("ALL CHECKS PASSED — this machine's path to the internet "
                "looks healthy right now. If the user still reports slowness, "
                "look at the specific app, Wi-Fi signal, or time-of-day "
                "patterns in the CSV log.")
    # The ladder order tells you WHERE it broke: gateway = local network,
    # DNS/public = beyond the local network.
    local = [n for n in failed if "Gateway" in n or "DNS server ping" in n]
    if local:
        return ("LOCAL NETWORK ISSUE — the machine can't reliably reach its "
                f"own gateway/DNS ({', '.join(local)}). Check cable/Wi-Fi, "
                "then the router, before blaming the internet.")
    return ("INTERNET ISSUE — local network is fine but something upstream "
            f"failed ({', '.join(failed)}). Likely ISP or remote-host side; "
            "escalate with the CSV log attached.")


def write_log(path, results):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "check", "result", "detail"])
        for name, ok, detail in results:
            status = "PASS" if ok else ("FAIL" if ok is False else "SKIP")
            w.writerow([stamp, name, status, detail])


def main():
    parser = argparse.ArgumentParser(
        description="Run the connectivity ladder (gateway, DNS, internet, "
                    "ports, traceroute) and print a plain-language verdict.")
    parser.add_argument("--host", default="www.google.com", metavar="HOST",
                        help="Host for the TCP port checks (default: "
                             "www.google.com)")
    parser.add_argument("--log", metavar="CSV",
                        help="Append timestamped results to CSV for trend "
                             "tracking")
    args = parser.parse_args()

    print("Running network diagnostics...\n")
    results = [
        check_ping("Gateway ping", get_gateway()),
        check_ping("DNS server ping", get_dns_server()),
        check_ping("Public host ping", "8.8.8.8"),
        check_dns(),
        check_tcp_port(args.host, 80),
        check_tcp_port(args.host, 443),
        check_traceroute("8.8.8.8"),
    ]

    for name, ok, detail in results:
        mark = "PASS" if ok else ("FAIL" if ok is False else "SKIP")
        print(f"[{mark}] {name}: {detail}")

    print(f"\n{summarize(results)}")

    if args.log:
        write_log(args.log, results)
        print(f"\nResults appended to {args.log}")


if __name__ == "__main__":
    main()
