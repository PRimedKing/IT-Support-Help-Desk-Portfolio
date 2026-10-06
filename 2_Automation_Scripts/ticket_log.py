"""Simple helpdesk ticket logger.

A tiny command-line ticket tracker for helpdesk practice: open tickets,
list them, and close them with resolution notes. Tickets are stored as
JSON in ticket_log.json next to this script. Standard library only.

Usage:
  python ticket_log.py add --requester "sam" --category printer --priority high --issue "Printer jams on every job"
  python ticket_log.py list
  python ticket_log.py list --status open
  python ticket_log.py show 3
  python ticket_log.py close 3 --resolution "Cleared jam, replaced worn feed roller"
"""

import argparse
import json
import os
import sys
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "ticket_log.json")
CATEGORIES = ["printer", "network", "password", "hardware", "software",
              "malware", "other"]
PRIORITIES = ["low", "medium", "high", "urgent"]
STATUSES = ["open", "closed"]


def load_tickets():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tickets(tickets):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2)


def next_id(tickets):
    return max((t["id"] for t in tickets), default=0) + 1


def cmd_add(args):
    tickets = load_tickets()
    ticket = {
        "id": next_id(tickets),
        "opened": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "requester": args.requester,
        "category": args.category,
        "priority": args.priority,
        "issue": args.issue,
        "status": "open",
        "closed": None,
        "resolution": None,
    }
    tickets.append(ticket)
    save_tickets(tickets)
    print("Ticket #%d opened (%s, %s priority)."
          % (ticket["id"], ticket["category"], ticket["priority"]))
    return 0


def cmd_list(args):
    tickets = load_tickets()
    if args.status:
        tickets = [t for t in tickets if t["status"] == args.status]
    if not tickets:
        print("No tickets found.")
        return 0
    print("%-4s %-16s %-10s %-9s %-8s %s"
          % ("ID", "Opened", "Category", "Priority", "Status", "Issue"))
    for t in tickets:
        print("%-4d %-16s %-10s %-9s %-8s %s"
              % (t["id"], t["opened"], t["category"], t["priority"],
                 t["status"], t["issue"][:60]))
    return 0


def cmd_show(args):
    for t in load_tickets():
        if t["id"] == args.id:
            for key in ("id", "opened", "requester", "category", "priority",
                        "issue", "status", "closed", "resolution"):
                print("%-10s: %s" % (key, t[key]))
            return 0
    print("Error: no ticket #%d." % args.id)
    return 1


def cmd_close(args):
    tickets = load_tickets()
    for t in tickets:
        if t["id"] == args.id:
            if t["status"] == "closed":
                print("Ticket #%d is already closed." % args.id)
                return 1
            t["status"] = "closed"
            t["closed"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            t["resolution"] = args.resolution
            save_tickets(tickets)
            print("Ticket #%d closed." % args.id)
            return 0
    print("Error: no ticket #%d." % args.id)
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="Log and track simple helpdesk tickets.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Open a new ticket.")
    p_add.add_argument("--requester", required=True, help="Who reported it.")
    p_add.add_argument("--category", required=True, choices=CATEGORIES)
    p_add.add_argument("--priority", default="medium", choices=PRIORITIES)
    p_add.add_argument("--issue", required=True, help="What is wrong.")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List tickets.")
    p_list.add_argument("--status", choices=STATUSES,
                       help="Filter by status.")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show one ticket in full.")
    p_show.add_argument("id", type=int, help="Ticket number.")
    p_show.set_defaults(func=cmd_show)

    p_close = sub.add_parser("close", help="Close a ticket.")
    p_close.add_argument("id", type=int, help="Ticket number.")
    p_close.add_argument("--resolution", required=True,
                         help="What fixed it.")
    p_close.set_defaults(func=cmd_close)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
