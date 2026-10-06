# Password Reset and Account Lockout

## Symptoms
- "Incorrect password" or "Account locked"
- User forgot password or it expired

## Before you touch anything
**Verify identity** using your organization's procedure (callback, manager approval, ID questions). Never reset a password for an unverified caller.

## Checks in order
1. **Simple causes:** Caps Lock, keyboard language, Num Lock, typing in the wrong field. Try typing the password in a plain text box to see it.
2. **Right account:** work account versus personal account, correct domain or email address.
3. **Locked or expired?**
   - Active Directory: open Active Directory Users and Computers, find the user, check the Account tab for a locked-out checkbox and the expiration date.
   - Microsoft 365 or Google Workspace: check the user in the admin console for a sign-in block or suspended status.
4. **Reset:**
   - Active Directory: right-click the user > Reset Password. Tick "User must change password at next logon." Tick "Unlock the user's account" if needed.
   - Microsoft 365 / Google Workspace: reset the password in the admin console and require a change at next sign-in.
   - Self-service: use the provider's "Forgot password" or account recovery option if enabled.
5. **Share the temporary password safely:** by phone or another approved channel, never in plain chat or email.
6. **Cached or saved credentials:** if the account keeps locking, an old password may be saved on a phone, mapped drive, or another device. Have the user update or remove it.

## Verify
User signs in successfully and sets a new password. Confirm mail and other apps still connect.

## Escalate
Repeated lockouts with no clear source, signs of a compromised account (unexpected sign-ins, mail rules the user didn't create), or accounts you don't have permission to modify.

## Prevent / document
Log who you verified, how, and what you reset. Remind the user about password managers and multi-factor authentication.
