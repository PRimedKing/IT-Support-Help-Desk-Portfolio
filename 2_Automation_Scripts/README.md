# Automation Scripts

Small Python scripts that check system values against expected thresholds and report pass/fail. Standard library only, no installs needed.

| Script | What it checks | Platform |
|---|---|---|
| `system_info_check.py` | OS, version, architecture, Python version vs. expected values | Windows / macOS / Linux |
| `disk_space_check.py` | Free space on each drive; flags any drive below 15% free | Windows / macOS / Linux |
| `driver_startup_check.py` | Unsigned drivers and number of startup programs | Windows |

## Usage

    python system_info_check.py
    python disk_space_check.py
    python driver_startup_check.py

Each script prints a report, appends it to a log file, and exits with code 1 if a check fails. Thresholds are constants at the top of each file.
