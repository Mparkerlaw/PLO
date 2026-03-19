"""Scheduler module — auto-poll CCAP and check deadlines on a timer."""

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from . import calendar_mod, ccap
from .config import DATA_DIR, ensure_data_dir

LOG_FILE = DATA_DIR / "scheduler_log.json"

# Default intervals (in seconds)
DEFAULT_CCAP_INTERVAL = 3600      # Check CCAP every hour
DEFAULT_REMINDER_INTERVAL = 1800  # Check deadlines every 30 minutes


class Scheduler:
    """Background scheduler that polls CCAP and checks deadlines."""

    def __init__(self, on_alert=None):
        """
        Args:
            on_alert: Callback function(alert_type, message) for notifications.
                      If None, alerts are only logged to file.
        """
        self.on_alert = on_alert or self._default_alert
        self._ccap_interval = DEFAULT_CCAP_INTERVAL
        self._reminder_interval = DEFAULT_REMINDER_INTERVAL
        self._running = False
        self._threads = []

    def start(self):
        """Start background polling threads."""
        if self._running:
            return
        self._running = True
        ensure_data_dir()

        ccap_thread = threading.Thread(target=self._ccap_loop, daemon=True)
        reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
        ccap_thread.start()
        reminder_thread.start()
        self._threads = [ccap_thread, reminder_thread]
        self._log("scheduler", "Started background scheduler")

    def stop(self):
        """Stop all polling."""
        self._running = False
        self._log("scheduler", "Stopped background scheduler")

    @property
    def is_running(self):
        return self._running

    def set_ccap_interval(self, seconds):
        """Change CCAP polling interval."""
        self._ccap_interval = max(300, seconds)  # Minimum 5 minutes

    def set_reminder_interval(self, seconds):
        """Change reminder check interval."""
        self._reminder_interval = max(60, seconds)  # Minimum 1 minute

    def _ccap_loop(self):
        """Periodically check CCAP for case updates."""
        while self._running:
            try:
                cases = ccap.list_cases()
                if cases:
                    results = ccap.check_all_cases()
                    for r in results:
                        if r.get("changed"):
                            msg = (
                                f"CCAP UPDATE: {r['case_name']} ({r['case_number']})\n"
                                f"  New status: {r['status']}"
                            )
                            self.on_alert("ccap_change", msg)
                            self._log("ccap_change", msg)
                        elif r.get("error"):
                            self._log("ccap_error", f"{r['case_number']}: {r['error']}")
                    self._log("ccap_check", f"Checked {len(results)} cases")
            except Exception as e:
                self._log("ccap_error", str(e))
            time.sleep(self._ccap_interval)

    def _reminder_loop(self):
        """Periodically check for approaching deadlines."""
        notified = set()  # Track what we've already alerted on this session
        while self._running:
            try:
                reminders = calendar_mod.get_reminders()
                for event in reminders:
                    event_key = f"{event['id']}_{event['date']}"
                    if event_key not in notified:
                        days = event.get("_days_away", "?")
                        if days == 0:
                            urgency = "TODAY"
                        elif days == 1:
                            urgency = "TOMORROW"
                        else:
                            urgency = f"in {days} days"
                        msg = (
                            f"DEADLINE {urgency}: {event['event_type'].replace('_', ' ').title()}\n"
                            f"  Case: {event['case_name']}\n"
                            f"  Date: {event['date']}\n"
                            f"  {event.get('description', '')}"
                        )
                        self.on_alert("deadline", msg)
                        self._log("deadline_alert", msg)
                        notified.add(event_key)
            except Exception as e:
                self._log("reminder_error", str(e))
            time.sleep(self._reminder_interval)

    def _log(self, event_type, message):
        """Append an entry to the scheduler log."""
        try:
            ensure_data_dir()
            log = []
            if LOG_FILE.exists():
                try:
                    log = json.loads(LOG_FILE.read_text())
                except (json.JSONDecodeError, FileNotFoundError):
                    log = []
            log.append({
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "message": message,
            })
            # Keep last 500 entries
            log = log[-500:]
            LOG_FILE.write_text(json.dumps(log, indent=2))
        except Exception:
            pass  # Don't crash the scheduler over logging

    def _default_alert(self, alert_type, message):
        """Default alert handler — print to console."""
        print(f"\n🔔 {message}\nPLO> ", end="", flush=True)


def get_recent_logs(count=20):
    """Read recent scheduler log entries."""
    try:
        if LOG_FILE.exists():
            log = json.loads(LOG_FILE.read_text())
            return log[-count:]
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    return []
