# Printer Won't Print

## Symptoms
- Print job sits in the queue or disappears
- "Printer offline" or error message
- Pages print blank, cut off or garbled

## Ask first
- What exactly happens? Did it ever work? What changed (new PC, update, moved Wi-Fi)?
- Does it fail in every app or just one?

## Checks in order
1. **Basics:** power on, paper loaded, ink/toner OK, no jam, no error light. Connected by USB cable, Ethernet or Wi-Fi?
2. **Isolate:** print a test or configuration page from the printer's own menu.
   - Works: the printer is fine, so the problem is the computer or the connection.
   - Fails: look at hardware, jams, ink/toner or printer errors.
3. **Right printer:** Settings > Bluetooth & devices > Printers & scanners. Make sure the correct printer is selected and set as default. Turn off "Use Offline" if it is checked.
4. **Clear the queue:** open the printer, choose "Open print queue," cancel all jobs, retry.
5. **Restart the Print Spooler** if jobs stay stuck. Open Command Prompt as administrator:
   ```
   net stop spooler
   net start spooler
   ```
   If jobs still won't clear, stop the spooler, delete the files in `C:\Windows\System32\spool\PRINTERS`, then start it again.
6. **Driver:** remove the printer, download the current driver from the manufacturer's site, reinstall.
7. **Network printers:** print the configuration page to find the IP address, then `ping <IP>`. No reply means a network problem. Make sure the computer is on the same network. If the printer's IP changed, re-add it by IP: Add device > "The printer that I want isn't listed" > Add using a TCP/IP address.
8. **macOS:** System Settings > Printers & Scanners, remove the printer and add it again.

## Verify
Print a real document with the user watching and confirm it looks right.

## Escalate
Hardware fault (jams that keep returning, error codes), a printer server or shared-printer permission problem, or a network issue that needs the network team.

## Prevent / document
Note the printer model, how it connects, the cause and the fix. Give the user a one-page guide for next time.
