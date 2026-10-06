# Slow Computer

## Symptoms
- Long boot times, freezing, apps taking forever to open

## Ask first
Slow all the time or only sometimes? Since when? Any new software, update or hardware change? Does one program cause it?

## Checks in order
1. **Restart:** many machines run for weeks without a restart.
2. **See what's busy:** press Ctrl+Shift+Esc to open Task Manager. Sort by CPU, Memory and Disk. One program using most of a resource is your lead.
3. **Startup apps:** Task Manager > Startup apps. Disable unneeded programs that launch at boot.
4. **Free disk space:** Settings > System > Storage. Below about 15% free hurts performance. Remove unused apps, empty the Recycle Bin, run Storage Sense.
5. **Updates:** install pending Windows and driver updates, and update the troublesome application.
6. **Malware:** run a full scan in Windows Security. Unexpected browser toolbars, pop-ups or high usage by unknown processes are warning signs.
7. **System file check** (Command Prompt as administrator):
   ```
   sfc /scannow
   ```
8. **Disk health:** a hard drive that clicks or shows errors may be failing. Back up data first.
9. **Hardware:** very little RAM or an old mechanical hard drive is often the real cause. Upgrading RAM or moving to an SSD can help a lot on older machines.
10. **Last resort:** reset or reinstall Windows after confirming the user's data is backed up.

## Verify
Restart and compare boot time and responsiveness with the user. Check Task Manager again.

## Escalate
Suspected failing hardware, signs of compromise, or machines that need replacement or reimaging under company policy.

## Prevent / document
Record what was found (low disk space, too many startup apps, etc.) and what changed. Suggest regular restarts and updates.
