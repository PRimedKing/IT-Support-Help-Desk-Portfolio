# printer-reset.py — Print spooler rescue for stuck queues

## What it does

Performs the standard print-spooler rescue ritual in one command: stops the
Print Spooler service, deletes the stuck job files in
`C:\Windows\System32\spool\PRINTERS`, restarts the service, and optionally
prints a test page. Every step is logged with timestamps for the ticket.

## Why a helpdesk tech wants it

"The printer isn't working" lands on the tier-1 queue daily, and half the time
the fix is this exact ritual. Doing it by hand means RDP-ing in, opening
services, finding the spool folder, and hoping you didn't miss a step. This
script makes the fix one command, identical every time, with a log you can
paste into the ticket as proof of what was tried.

## Requirements

- **Windows only** — it controls the Windows Print Spooler service. On any
  other OS it exits immediately with a clear message and changes nothing.
- Python 3.8+ (standard library only)
- **Administrator rights** — stopping/starting services requires an elevated
  command prompt. The script warns you if you're not elevated.

## Step-by-step usage

**1. Get the file** — copy `printer-reset.py` to the affected Windows machine.

**2. Open an Administrator command prompt** (right-click → *Run as
administrator*) and dry-run first:

```cmd
python printer-reset.py
```

**3. Read the plan**, then execute it for real:

```cmd
python printer-reset.py --yes
```

Realistic example output (dry run):

```
=== Print spooler rescue plan ===

  1. Stop the Print Spooler service
  2. Delete 3 stuck job file(s) from C:\Windows\System32\spool\PRINTERS
       - C:\Windows\System32\spool\PRINTERS\00014.SHD
       - C:\Windows\System32\spool\PRINTERS\00014.SPL
       - C:\Windows\System32\spool\PRINTERS\00015.SHD
  3. Start the Print Spooler service

DRY RUN — nothing was changed. Re-run with --yes to execute.
```

And with `--yes`, each step runs with a timestamped log:

```
[14:22:01] Starting spooler reset (--yes confirmed)
[14:22:01] >>> Stopping Print Spooler
[14:22:03]     OK
[14:22:03] Deleting 3 file(s) from spool folder
[14:22:03]     deleted C:\Windows\System32\spool\PRINTERS\00014.SHD
...
[14:22:05] Spooler reset complete. If printing still fails, the problem is
upstream (driver, network, or the printer itself) — escalate with the log
above attached to the ticket.
```

To also print a test page on the default printer afterward:

```cmd
python printer-reset.py --yes --test-page
```

## Safety notes

- **Dry-run is the default.** Without `--yes`, the script only lists what it
  *would* do — it never touches services or files.
- It only deletes files inside the spool `PRINTERS` folder (stuck print jobs),
  never anything else.
- Needs an Administrator prompt; without one, the service commands fail and
  the log tells you exactly why.
- If printing still fails after a clean reset, the script's closing message
  says so plainly and tells you what to escalate — it never pretends a deeper
  problem is fixed.
