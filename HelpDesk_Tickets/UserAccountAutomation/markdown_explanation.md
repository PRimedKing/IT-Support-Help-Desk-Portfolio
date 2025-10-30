# User Account Automation

## Purpose
Automates new user onboarding and departing user offboarding processes.

## Functions
- Creates user accounts, assigns default groups, and provisions access.
- Sends welcome or exit emails automatically.
- Logs all changes to prevent orphaned accounts.

## Use Case
New employee joins → script runs → AD credentials created → access email sent.

## Security
Implements check for existing usernames and encrypts logs.
