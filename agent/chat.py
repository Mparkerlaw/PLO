"""PLO Agent — Chat-based legal practice assistant.

This is the main entry point. Run with: python -m agent.chat
"""

import sys
from datetime import datetime

from . import calendar_mod, ccap, workflows
from .ai_chat import AIChat
from .config import ensure_data_dir
from .drafter import list_templates, get_template_fields, interactive_draft
from .reminders import (
    configure_email, configure_sms, get_notify_status, send_alert,
)
from .scheduler import Scheduler, get_recent_logs

BANNER = """
╔══════════════════════════════════════════════════╗
║   PLO Agent — Parker Law Office Assistant        ║
║   Criminal Defense & Family Law | Wisconsin      ║
║   ─────────────────────────────────────────────  ║
║   OpenClaw Agent v0.2                            ║
╚══════════════════════════════════════════════════╝

Commands:
  calendar     — View upcoming events and reminders
  add event    — Add a court date or deadline
  cases        — List monitored CCAP cases
  add case     — Add a case to CCAP monitoring
  check ccap   — Check all cases for updates
  intake       — Start client intake workflow
  stages       — Show case stages and tasks
  playbook     — View a practice playbook
  draft        — Draft a document from a template
  templates    — List available document templates
  notify       — Configure email/SMS reminders
  scheduler    — Start/stop background CCAP polling
  logs         — View recent scheduler activity
  ai on/off    — Toggle AI chat mode (needs API key)
  help         — Show this help message
  quit         — Exit

Or just type naturally — I'll figure out what you need.
"""

HELP_TEXT = BANNER


def main():
    """Run the interactive chat loop."""
    ensure_data_dir()
    print(BANNER)

    # Initialize AI chat
    ai = AIChat()
    ai_mode = ai.available  # Auto-enable if API key is set
    if ai_mode:
        print("🤖 AI chat: ON (Claude connected)\n")
    else:
        print("💬 AI chat: OFF (set ANTHROPIC_API_KEY to enable)\n")

    # Initialize scheduler (not started by default)
    scheduler = Scheduler(on_alert=_make_alert_handler())

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
            scheduler.stop()
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        # ── Direct commands ──────────────────────────────────────
        if cmd in ("quit", "exit", "q"):
            print("Goodbye.")
            scheduler.stop()
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

        # ── Document drafting ────────────────────────────────────
        elif cmd in ("templates", "list templates"):
            handle_list_templates()
        elif cmd.startswith("draft"):
            handle_draft(cmd)

        # ── Notifications ────────────────────────────────────────
        elif cmd.startswith("notify"):
            handle_notify(cmd)

        # ── Scheduler ────────────────────────────────────────────
        elif cmd in ("scheduler start", "start scheduler", "autopoll"):
            scheduler.start()
            print("Background scheduler started (CCAP polling + deadline checks).")
        elif cmd in ("scheduler stop", "stop scheduler"):
            scheduler.stop()
            print("Background scheduler stopped.")
        elif cmd in ("scheduler", "scheduler status"):
            status = "running" if scheduler.is_running else "stopped"
            print(f"Scheduler: {status}")
        elif cmd in ("logs", "log", "scheduler logs"):
            handle_logs()

        # ── AI mode toggle ───────────────────────────────────────
        elif cmd in ("ai on", "ai enable"):
            if ai.available:
                ai_mode = True
                print("🤖 AI chat mode: ON")
            else:
                print("Set ANTHROPIC_API_KEY first: export ANTHROPIC_API_KEY=your-key")
        elif cmd in ("ai off", "ai disable"):
            ai_mode = False
            print("💬 AI chat mode: OFF (using keyword matching)")
        elif cmd in ("ai reset", "reset ai", "new chat"):
            ai.reset()
            print("AI conversation reset.")

        # ── Natural language / AI chat ───────────────────────────
        else:
            if ai_mode and ai.available:
                response = ai.chat(user_input)
                print(f"\n{response}\n")
            else:
                handle_natural(user_input)


def _make_alert_handler():
    """Create an alert handler that also sends notifications."""
    def handler(alert_type, message):
        # Print to console
        print(f"\n🔔 {message}\nPLO> ", end="", flush=True)
        # Also send via configured channels
        try:
            send_alert(alert_type, message)
        except Exception:
            pass
    return handler


# ── Command Handlers ─────────────────────────────────────────────────

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
        from pathlib import Path
        playbook_dir = Path(__file__).resolve().parent.parent / "playbooks"
        if playbook_dir.exists():
            available = [f.stem for f in playbook_dir.glob("*.md")]
            if available:
                print(f"  Available: {', '.join(available)}")
    print()


def handle_list_templates():
    """Show available document templates."""
    templates = list_templates()
    if not templates:
        print("No templates found in templates/ directory.")
        return
    print(f"\n📄 Available Templates ({len(templates)}):\n")
    for name in templates:
        fields = get_template_fields(name)
        print(f"  {name}")
        if fields:
            print(f"    Fields: {', '.join(fields)}")
    print(f"\n  Use 'draft <template-name>' to fill one in.\n")


def handle_draft(cmd):
    """Draft a document from a template."""
    parts = cmd.split(maxsplit=1)
    if len(parts) > 1:
        name = parts[1].strip()
    else:
        templates = list_templates()
        if templates:
            print(f"  Available templates: {', '.join(templates)}")
        name = input("  Template name: ").strip()

    if not name:
        print("Cancelled.")
        return

    output_path, content = interactive_draft(name)
    if output_path:
        print(f"\n  ✓ Draft saved to: {output_path}\n")
    else:
        print(f"\n  {content}\n")


def handle_notify(cmd):
    """Configure or view notification settings."""
    parts = cmd.split()
    if len(parts) <= 1:
        print(f"\n— Notification Status —\n  {get_notify_status()}")
        print("\n  Commands:")
        print("    notify email  — Configure email alerts")
        print("    notify sms    — Configure SMS alerts")
        print("    notify test   — Send a test notification\n")
        return

    subcmd = parts[1]

    if subcmd == "email":
        print("\n— Configure Email Notifications —")
        smtp_host = input("  SMTP host (e.g. smtp.gmail.com): ").strip()
        smtp_port = input("  SMTP port (default 587): ").strip()
        smtp_port = int(smtp_port) if smtp_port.isdigit() else 587
        username = input("  Username/email: ").strip()
        password = input("  Password/app password: ").strip()
        from_addr = input("  From address: ").strip() or username
        to_addr = input("  Send alerts to: ").strip()
        configure_email(smtp_host, smtp_port, username, password, from_addr, to_addr)
        print("  ✓ Email notifications configured.\n")

    elif subcmd == "sms":
        print("\n— Configure SMS Notifications —")
        print("  (Uses carrier email gateway — requires email to be configured first)")
        phone = input("  Phone number (10 digits): ").strip().replace("-", "").replace(" ", "")
        carrier = input("  Carrier (att/verizon/tmobile/sprint/uscellular): ").strip()
        success, msg = configure_sms(phone, carrier)
        if success:
            print(f"  ✓ {msg}\n")
        else:
            print(f"  ✗ {msg}\n")

    elif subcmd == "test":
        print("  Sending test notification...")
        results = send_alert("test", "This is a test alert from PLO Agent.")
        for channel, success in results.items():
            status = "✓ sent" if success else "✗ failed"
            print(f"  {channel}: {status}")
        if not results:
            print("  No notification channels configured. Use 'notify email' or 'notify sms' first.")
        print()


def handle_logs():
    """Show recent scheduler log entries."""
    logs = get_recent_logs(20)
    if not logs:
        print("No scheduler logs yet.")
        return
    print("\n— Recent Scheduler Activity —\n")
    for entry in logs:
        ts = entry["timestamp"][:16].replace("T", " ")
        print(f"  {ts} | {entry['type']} | {entry['message'][:80]}")
    print()


def handle_natural(text):
    """Handle natural language input with keyword matching."""
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
    elif any(w in lower for w in ["draft", "template", "letter", "motion"]):
        if "list" in lower or "template" in lower:
            handle_list_templates()
        else:
            handle_draft(f"draft")
    elif any(w in lower for w in ["notify", "reminder", "alert", "email", "sms"]):
        handle_notify("notify")
    else:
        print(
            "  I'm not sure what you need. Type 'help' to see available commands.\n"
            "  Tip: Set ANTHROPIC_API_KEY and type 'ai on' for full AI chat."
        )


if __name__ == "__main__":
    main()
