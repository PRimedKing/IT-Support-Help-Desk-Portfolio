# Case: Design workstation takes 10+ minutes to boot

**Date:** 2025
**Environment:** Windows 10 design workstation, small production office
**Reported by:** colleague (no names)

## Problem
Machine took over ten minutes to reach the desktop, and design apps were unusable for another ten after that.

## What I asked and checked
1. When did it start? Gradually over months, worse the last few weeks.
2. Task Manager after boot: disk pinned at 100% for a long stretch, with nothing obviously hogging it.
3. Startup apps: 23 programs launching at boot, most of them updaters and helpers nobody needed.
4. Disk health: the drive was an old mechanical HDD, and it was starting to show reallocated sectors in its SMART data.

## Cause
A dying mechanical hard drive combined with years of accumulated startup bloat. The disk was the bottleneck for everything.

## Fix
1. Backed up the user's files first — a failing drive means backup before anything else.
2. Cloned the drive to a new SSD.
3. Disabled the unneeded startup programs (left antivirus and the design apps' licensing services).
4. Verified TRIM was enabled on the SSD and ran updates.

## Result
Boot time dropped to under a minute. The colleague confirmed apps opened normally the next morning.

## What I'd do differently or document
Check disk health sooner — I spent time on startup apps before looking at SMART data, and the drive was the real story. Wrote this up as the example for the slow-computer guide in this repo.
