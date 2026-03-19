"""Calendar module — track court dates, deadlines, and follow-ups."""

import uuid
from datetime import datetime, timedelta

from .config import CALENDAR_FILE, load_json, save_json

# Event types relevant to criminal defense and family law
EVENT_TYPES = [
    "court_hearing",
    "filing_deadline",
    "statute_of_limitations",
    "client_meeting",
    "follow_up",
    "discovery_deadline",
    "plea_hearing",
    "sentencing",
    "custody_hearing",
    "mediation",
    "other",
]


def add_event(case_name, event_type, date_str, description="", remind_days=3):
    """Add a calendar event.

    Args:
        case_name: Client or case identifier (no confidential details).
        event_type: One of EVENT_TYPES.
        date_str: Date in YYYY-MM-DD format.
        description: Brief note about the event.
        remind_days: How many days before to trigger a reminder.

    Returns:
        The created event dict.
    """
    events = load_json(CALENDAR_FILE)
    event = {
        "id": str(uuid.uuid4())[:8],
        "case_name": case_name,
        "event_type": event_type,
        "date": date_str,
        "description": description,
        "remind_days": remind_days,
        "created": datetime.now().isoformat(),
        "completed": False,
    }
    events.append(event)
    save_json(CALENDAR_FILE, events)
    return event


def get_upcoming(days=14):
    """Return events within the next N days, sorted by date."""
    events = load_json(CALENDAR_FILE)
    today = datetime.now().date()
    cutoff = today + timedelta(days=days)
    upcoming = []
    for e in events:
        if e.get("completed"):
            continue
        try:
            event_date = datetime.strptime(e["date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if today <= event_date <= cutoff:
            e["_days_away"] = (event_date - today).days
            upcoming.append(e)
    return sorted(upcoming, key=lambda x: x["date"])


def get_reminders():
    """Return events that are within their reminder window."""
    events = load_json(CALENDAR_FILE)
    today = datetime.now().date()
    reminders = []
    for e in events:
        if e.get("completed"):
            continue
        try:
            event_date = datetime.strptime(e["date"], "%Y-%m-%d").date()
            remind_days = e.get("remind_days", 3)
        except (ValueError, KeyError):
            continue
        days_until = (event_date - today).days
        if 0 <= days_until <= remind_days:
            e["_days_away"] = days_until
            reminders.append(e)
    return sorted(reminders, key=lambda x: x["date"])


def mark_complete(event_id):
    """Mark an event as completed."""
    events = load_json(CALENDAR_FILE)
    for e in events:
        if e["id"] == event_id:
            e["completed"] = True
            save_json(CALENDAR_FILE, events)
            return True
    return False


def remove_event(event_id):
    """Remove an event entirely."""
    events = load_json(CALENDAR_FILE)
    events = [e for e in events if e["id"] != event_id]
    save_json(CALENDAR_FILE, events)


def get_events_for_case(case_name):
    """Return all events for a given case."""
    events = load_json(CALENDAR_FILE)
    return [e for e in events if e["case_name"].lower() == case_name.lower()]


def format_event(event):
    """Format an event for display."""
    days = event.get("_days_away")
    urgency = ""
    if days is not None:
        if days == 0:
            urgency = " ⚠️  TODAY"
        elif days == 1:
            urgency = " ⚠️  TOMORROW"
        elif days <= 3:
            urgency = f" ⏰ in {days} days"
        else:
            urgency = f" ({days} days away)"

    return (
        f"  [{event['id']}] {event['date']}{urgency}\n"
        f"    {event['event_type'].replace('_', ' ').title()} — {event['case_name']}\n"
        f"    {event.get('description', '')}"
    )
