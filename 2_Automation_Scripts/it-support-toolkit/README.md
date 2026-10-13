# IT Support Toolkit

Four small Python tools that automate the most common tier-1 helpdesk work:
ticket triage, password-expiry warnings, print spooler rescue, and network
troubleshooting. Written for real desks, not for demo day.

## What this proves

If you're reading this as a hiring manager, here's what these four scripts
are meant to demonstrate:

- **Python scripting for operations** — every tool is standard-library-only
  (`subprocess`, `socket`, `smtplib`, `csv`, `ctypes`). No pip installs, no
  frameworks; they run on any stock Python 3 install, which is exactly the
  constraint you face on locked-down corporate machines.
- **Troubleshooting mindset** — each tool encodes a real diagnostic workflow
  (the connectivity ladder, the spooler ritual, the "what would I ask first?"
  snapshot), not just code that runs.
- **Safety habits** — destructive actions default to dry-run and require an
  explicit `--yes`/`--send`; everything logs what it did for the ticket.
- **Documentation habits** — every tool ships a README with step-by-step
  usage a non-technical tech can follow.

## Author background

Elijah Carrasquillo — IT support specialist with a background in
mechanical/aerospace engineering and graphic design & marketing, backed by 5+
years hands-on end-user support (primary technical troubleshooter at HomeWetBar
2020–2026; tech support lead at Oklahoma State University 2017–2019).
Google IT Support Professional Certificate; CompTIA A+ in progress. These
tools automate workflows from that experience.

## Folder map

```
it-support-toolkit/
├── README.md                      # you are here
├── ticket-snapshot/
│   ├── triage-snapshot.py         # one-command system snapshot for tickets
│   └── README.md
├── password-expiry-notifier/
│   ├── expiry-notifier.py         # warn users before passwords expire
│   ├── users.csv                  # sample input (replace with your own)
│   └── README.md
├── printer-reset/
│   ├── printer-reset.py           # Windows print spooler rescue
│   └── README.md
└── network-diagnostics/
    ├── netdiag.py                 # connectivity ladder + CSV trend logging
    └── README.md
```

## Quickstart

```bash
git clone <this-repo>
cd it-support-toolkit
# pick a tool, open its folder, follow its README — each is standalone:
python ticket-snapshot/triage-snapshot.py --help
```

Each tool is independent: copy any single folder to a machine and it runs.

## The tools, one line each

| Tool | One-liner |
| ---- | --------- |
| `ticket-snapshot` | Answers the first 10 minutes of triage questions in one command — paste the markdown straight into the ticket. |
| `password-expiry-notifier` | Emails users at 14/7/3/1 days before password expiry; dry-run by default, so the #1 preventable ticket stops happening. |
| `printer-reset` | The stuck-queue ritual (stop spooler → clear jobs → restart) as one safe, logged, Windows command. |
| `network-diagnostics` | Turns "the internet is slow" into PASS/FAIL evidence with CSV trend logging for intermittent issues. |

## Production notes (honest version)

These are portfolio tools, built to be read and run as-is. To use them in
production you'd want:

- **password-expiry-notifier**: swap the CSV reader for a direct Active
  Directory query (`ldap3`, reading `pwdLastSet`) — the tool's README
  documents the exact integration path. Run it daily from Task Scheduler as
  a service account; pull SMTP creds from a vault, not the command line.
- **Scheduling**: `netdiag --log` and the notifier are designed for Task
  Scheduler / cron. The snapshot and printer reset are on-demand tech tools.
- **printer-reset**: fine as-is on Windows fleets; wrap it in your RMM
  (Datto, NinjaOne, etc.) for remote execution.
- **ticket-snapshot**: pipe `--json` into your ticketing system's API to
  auto-attach snapshots to new tickets.

No telemetry, no network calls home, no dependencies to audit — that's
deliberate. Helpdesk tools should be boring and trustworthy.
