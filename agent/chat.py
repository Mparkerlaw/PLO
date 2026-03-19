"""PLO Agent — Chat-based legal practice assistant.

This is the main entry point. Run with: python -m agent.chat
"""

import sys
from datetime import datetime

from . import calendar_mod, ccap, workflows
from .config import ensure_data_dir

BANNER = """
╔══════════════════════════════════════════════╗
║   PLO Agent — Parker Law Office Assistant    ║
║   Criminal Defense & Family Law              ║
╚══════════════════════════════════════════════╝

Commands:
  calendar   — View upcoming events and reminders
  add event  — Add a court date or deadline
  cases      — List monitored CCAP cases
  add case   — Add a case to CCAP monitoring
  check ccap — Check all cases for updates
  intake     — Start client intake workflow
  stages     — Show case stages and tasks
  playbook   — View a practice playbook
  help       — Show this help message
  quit       — Exit

Or just type naturally — I'll figure out what you need.
"""

HELP_TEXT = BANNER


def main():
    """Run the interactive chat loop."""
    ensure_data_dir()
    print(BANNER)

    # Show reminders on startup
    reminders = calendar_mod.get_reminders()
    if reminders:
        print("📋 REMINDERS:")
        for event in reminders:
            print(calendar_mod.format_event(event))
        print()

    while True:
        try:
            user_input = input("PLO> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("quit", "exit", "q"):
            print("Goodbye.")
            break
        elif cmd in ("help", "h", "?"):
            print(HELP_TEXT)
        elif cmd in ("calendar", "cal", "upcoming", "dates"):
            handle_calendar()
        elif cmd.startswith("add event") or cmd.startswith("new event"):
            handle_add_event()
        elif cmd in ("cases", "my cases", "list cases"):
            handle_list_cases()
        elif cmd.startswith("add case") or cmd.startswith("new case"):
            handle_add_case()
        elif cmd in ("check ccap", "ccap", "check cases", "updates"):
            handle_check_ccap()
        elif cmd.startswith("intake"):
            handle_intake(cmd)
        elif cmd.startswith("stages") or cmd.startswith("stage"):
            handle_stages(cmd)
        elif cmd.startswith("playbook"):
            handle_playbook(cmd)
        elif cmd.startswith("complete ") or cmd.startswith("done "):
            event_id = cmd.split()[-1]
            if calendar_mod.mark_complete(event_id):
                print(f"Marked {event_id} as complete.")
            else:
                print(f"Event {event_id} not found.")
        elif cmd.startswith("remove event "):
            event_id = cmd.split()[-1]
            calendar_mod.remove_event(event_id)
            print(f"Removed event {event_id}.")
        elif cmd.startswith("remove case "):
            case_no = cmd.split("remove case ")[-1].strip()
            ccap.remove_case(case_no)
            print(f"Stopped monitoring {case_no}.")
        else:
            handle_natural(user_input)


def handle_calendar():
    """Show upcoming events."""
    events = calendar_mod.get_upcoming(days=30)
    if not events:
        print("No upcoming events in the next 30 days.")
        return
    print(f"\n📅 Upcoming Events ({len(events)}):\n")
    for event in events:
        print(calendar_mod.format_event(event))
    print()


def handle_add_event():
    """Walk through adding a calendar event."""
    print("\n— Add Calendar Event —")
    case_name = input("  Case name/reference: ").strip()
    if not case_name:
        print("Cancelled.")
        return

    print(f"  Event types: {', '.join(calendar_mod.EVENT_TYPES)}")
    event_type = input("  Event type: ").strip().lower().replace(" ", "_")
    if event_type not in calendar_mod.EVENT_TYPES:
        print(f"  Unknown type, using 'other'.")
        event_type = "other"

    date_str = input("  Date (YYYY-MM-DD): ").strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("  Invalid date format. Cancelled.")
        return

    description = input("  Description (optional): ").strip()
    remind = input("  Remind days before (default 3): ").strip()
    remind_days = int(remind) if remind.isdigit() else 3

    event = calendar_mod.add_event(case_name, event_type, date_str, description, remind_days)
    print(f"\n  ✓ Event added [{event['id']}]")
    print(calendar_mod.format_event(event))
    print()


def handle_list_cases():
    """Show all monitored CCAP cases."""
    cases = ccap.list_cases()
    if not cases:
        print("No cases being monitored. Use 'add case' to add one.")
        return
    print(f"\n📂 Monitored Cases ({len(cases)}):\n")
    for c in cases:
        checked = c.get("last_checked", "never")
        if checked != "never":
            checked = checked[:16].replace("T", " ")
        status = c.get("last_status", "not checked yet")
        print(f"  {c['case_number']} ({c['county']} Co.) — {c['case_name']}")
        print(f"    Type: {c['case_type']} | Last checked: {checked}")
        if status:
            print(f"    Status: {status}")
        print()


def handle_add_case():
    """Walk through adding a case to CCAP monitoring."""
    print("\n— Add Case to CCAP Monitor —")
    case_name = input("  Case reference (initials or short name): ").strip()
    if not case_name:
        print("Cancelled.")
        return
    county = input("  County: ").strip()
    case_number = input("  Case number (e.g. 2025CF001234): ").strip()
    case_type = input("  Type (criminal/family): ").strip().lower()
    if case_type not in ("criminal", "family"):
        case_type = "criminal"

    result = ccap.add_case(case_name, county, case_number, case_type)
    if result:
        print(f"\n  ✓ Now monitoring {case_number} ({county} Co.)")
    else:
        print(f"\n  Already monitoring {case_number}.")
    print()


def handle_check_ccap():
    """Check all monitored cases on CCAP."""
    cases = ccap.list_cases()
    if not cases:
        print("No cases to check. Use 'add case' first.")
        return
    print("\nChecking CCAP...")
    results = ccap.check_all_cases()
    for r in results:
        marker = " 🔔 CHANGED" if r.get("changed") else ""
        if "error" in r:
            print(f"  {r['case_number']} — {r['case_name']}: ⚠ {r['error']}")
        else:
            print(f"  {r['case_number']} — {r['case_name']}: {r['status']}{marker}")
    print()


def handle_intake(cmd):
    """Run client intake workflow."""
    parts = cmd.split()
    if len(parts) > 1:
        case_type = parts[1]
    else:
        case_type = input("  Case type (criminal/family): ").strip().lower()

    questions = workflows.get_intake_questions(case_type)
    print(f"\n— {case_type.title()} Intake ({len(questions)} questions) —\n")
    answers = {}
    for i, q in enumerate(questions, 1):
        answer = input(f"  {i}. {q}\n     > ").strip()
        answers[q] = answer

    print("\n— Intake Summary —")
    for q, a in answers.items():
        print(f"  Q: {q}")
        print(f"  A: {a}\n")

    add_to_cal = input("  Add next court date to calendar? (y/n): ").strip().lower()
    if add_to_cal == "y":
        handle_add_event()

    add_to_ccap = input("  Add to CCAP monitoring? (y/n): ").strip().lower()
    if add_to_ccap == "y":
        handle_add_case()

    print("  ✓ Intake complete.\n")


def handle_stages(cmd):
    """Show case stages and tasks for a case type."""
    parts = cmd.split()
    if len(parts) > 1:
        case_type = parts[1]
    else:
        case_type = input("  Case type (criminal/family): ").strip().lower()

    stages = workflows.get_case_stages(case_type)
    if not stages:
        print("  Unknown case type.")
        return

    print(f"\n— {case_type.title()} Case Stages —\n")
    for i, stage in enumerate(stages, 1):
        tasks = workflows.get_stage_tasks(case_type, stage)
        print(f"  {i}. {stage.replace('_', ' ').title()}")
        for task in tasks:
            print(f"     • {task}")
    print()


def handle_playbook(cmd):
    """Load and display a playbook."""
    parts = cmd.split(maxsplit=1)
    if len(parts) > 1:
        name = parts[1].strip()
    else:
        name = input("  Playbook name (e.g. client-intake): ").strip()

    content = workflows.load_playbook(name)
    if content:
        print(f"\n{content}")
    else:
        print(f"  Playbook '{name}' not found.")
        # List available playbooks
        from .config import DATA_DIR
        playbook_dir = DATA_DIR.parent / "playbooks"
        if playbook_dir.exists():
            available = [f.stem for f in playbook_dir.glob("*.md")]
            if available:
                print(f"  Available: {', '.join(available)}")
    print()


def handle_natural(text):
    """Handle natural language input with simple keyword matching.

    This is a placeholder for future AI/LLM integration.
    For now it maps common phrases to commands.
    """
    lower = text.lower()

    if any(w in lower for w in ["court date", "hearing", "deadline", "when"]):
        handle_calendar()
    elif any(w in lower for w in ["new client", "intake", "onboard"]):
        if "family" in lower or "divorce" in lower or "custody" in lower:
            handle_intake("intake family")
        else:
            handle_intake("intake criminal")
    elif any(w in lower for w in ["ccap", "check", "update", "status"]):
        handle_check_ccap()
    elif any(w in lower for w in ["add", "schedule", "new event"]):
        handle_add_event()
    else:
        print(
            "  I'm not sure what you need. Type 'help' to see available commands.\n"
            "  (Future versions will have full AI chat — stay tuned!)"
        )


if __name__ == "__main__":
    main()
