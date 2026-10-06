# No Internet / Can't Connect to Wi-Fi

## Symptoms
- "No internet," "Connected, no internet," or can't see the network
- Some sites load and others don't

## Ask first
Is it one device or several? Just one app? Did it work earlier today? Anything change (move, update, new router)?

## Checks in order
1. **Scope it:** try another device on the same network. If everything is down, suspect the router, modem or ISP. If only one device fails, focus on that device.
2. **Basics:** airplane mode off, Wi-Fi switch on, correct network chosen, Ethernet cable seated.
3. **Reconnect:** disconnect, "Forget" the network, then join again and re-enter the password.
4. **Restart:** the device, then the router and modem (unplug about 30 seconds, plug back in, wait a few minutes).
5. **Check the IP address:** open Command Prompt and run `ipconfig`.
   - An address starting with `169.254` means the device did not get an address from DHCP. Check the router.
6. **Renew the connection:**
   ```
   ipconfig /release
   ipconfig /renew
   ipconfig /flushdns
   ```
7. **Separate DNS from connection:**
   ```
   ping 8.8.8.8
   ping google.com
   ```
   - First works, second fails: a DNS problem. Try different DNS servers or flush DNS again.
   - Both fail: the connection itself is down.
8. **Reset the network stack** (Command Prompt as administrator, then restart):
   ```
   netsh winsock reset
   netsh int ip reset
   ```
9. **Adapter and driver:** run the Windows network troubleshooter, check Device Manager for errors, update or reinstall the adapter driver.

## Verify
Open a few websites and one app that needs internet. Confirm the connection stays up for a few minutes.

## Escalate
Router or modem fault, ISP outage, or a company network issue (VLAN, firewall, MAC filtering) for the network team.

## Prevent / document
Record the device, the symptoms, and which step fixed it. Note signal strength problems, which may call for moving the router or access point.
