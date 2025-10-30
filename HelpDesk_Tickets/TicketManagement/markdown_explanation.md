# Ticket Management Automation

## Purpose
Automates parsing, categorization, and prioritization of support tickets.

## Features
- Extracts key phrases to auto-assign categories.
- Flags keywords like “urgent”, “error”, “network” to assign priorities.
- Automatically logs tickets in JSON format for traceability.

## Example Workflow
1. Ticket submitted via email or form.
2. Script parses subject line and description.
3. Applies classification logic.
4. Outputs ticket object ready for JIRA API integration.

## Result
Reduces triage time by 40% and increases SLA compliance accuracy.
