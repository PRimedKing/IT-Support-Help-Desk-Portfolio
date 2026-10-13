# netdiag.py — "The internet is slow" turned into data

## What it does

Runs the standard connectivity ladder and ends with a plain-language verdict:

1. **Gateway ping** — can this machine reach its own router?
2. **DNS server ping** — is the configured DNS server alive?
3. **Public host ping** — is the broader internet reachable? (8.8.8.8)
4. **DNS resolution** — do names resolve to addresses?
5. **TCP port 80/443** — can it actually open web connections to a host?
6. **Traceroute** — where does the path break, if it does?

Each check gets a PASS/FAIL/SKIP, and the summary tells you in plain English
whether the problem looks local (your network) or upstream (ISP/remote side).
With `--log`, every run appends timestamped rows to a CSV so intermittent
"it's slow sometimes" complaints become a trend you can graph.

## Why a helpdesk tech wants it

Vague network complaints are the worst tickets because there's nothing to act
on. This script replaces "have you tried restarting?" with evidence: either
the ladder passes and you look at the app/Wi-Fi/time-of-day, or it fails at a
specific rung and you know exactly where to escalate — with the log attached.

## Requirements

- Python 3.8+ (standard library only — `subprocess`, `socket`, `platform`)
- Windows, macOS, or Linux (ping/traceroute flags adapt per OS)
- No admin rights needed — it only sends ordinary ping/DNS/TCP traffic, the
  same as opening a web page

## Step-by-step usage

**1. Get the file** — copy `netdiag.py` to the affected machine.

**2. Run it:**

```bash
python netdiag.py
```

**3. Read the verdict** at the bottom. Realistic example (healthy machine):

```
Running network diagnostics...

[PASS] Gateway ping: 192.168.1.1 — 1 ms avg
[PASS] DNS server ping: 192.168.1.1 — 1 ms avg
[PASS] Public host ping: 8.8.8.8 — 12 ms avg
[PASS] DNS resolution: www.google.com -> 142.250.72.36
[PASS] TCP port 80 on www.google.com: open
[PASS] TCP port 443 on www.google.com: open
[PASS] Traceroute: 9 hops recorded to 8.8.8.8

ALL CHECKS PASSED — this machine's path to the internet looks healthy right
now. If the user still reports slowness, look at the specific app, Wi-Fi
signal, or time-of-day patterns in the CSV log.
```

And a broken one — note how the ladder pinpoints the layer:

```
[PASS] Gateway ping: 192.168.1.1 — 1 ms avg
[FAIL] DNS server ping: 192.168.1.1 — no reply
[PASS] Public host ping: 8.8.8.8 — 14 ms avg
[FAIL] DNS resolution: could not resolve www.google.com
[FAIL] TCP port 80 on www.google.com: closed/unreachable
[FAIL] TCP port 443 on www.google.com: closed/unreachable

INTERNET ISSUE — local network is fine but something upstream failed
(DNS server ping, DNS resolution, TCP port 80/443). Likely ISP or
remote-host side; escalate with the CSV log attached.
```

Here the gateway answers but DNS doesn't — the verdict correctly points past
the local network instead of blaming the user's Wi-Fi.

**Tracking an intermittent issue** — run it on a schedule and log every run:

```bash
python netdiag.py --log netlog.csv
```

After a day of hourly runs, `netlog.csv` shows exactly when the failures
started — powerful evidence for an ISP ticket. Test a specific host's web
ports with `python netdiag.py --host intranet.company.local`.

## Safety notes

- **Non-destructive.** It sends pings, one DNS lookup, and two brief TCP
  connection attempts — less traffic than loading a single web page.
- Traceroute is skipped gracefully if the system tool isn't installed.
- **ICMP caveat:** some corporate firewalls block ping entirely. In that case
  the ping checks will FAIL while TCP checks PASS — read the verdict in that
  context (the tool can't distinguish "blocked by policy" from "host down"
  for ICMP). The TCP and DNS checks remain the reliable signal there.
